# =========================
# FLASK & AUTH IMPORTS
# =========================
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Flask-Login handles user authentication (login/logout/session)
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)

# Used to securely hash and verify passwords
from werkzeug.security import generate_password_hash, check_password_hash


# =========================
# APP MODULE IMPORTS
# =========================
from models import db, User, UserPreference, News, Comment


# Fetches news from NewsAPI and stores in DB
from news_api_client import fetch_and_cache_news_for_user

# AI-based realtime news search
from ai_news_bot import ai_realtime_news

# Perplexity AI based fact-checker
from perplexity_news_verifier import classify_news_transformer

from dotenv import load_dotenv
import os

# =========================
# APP CONFIGURATION
# =========================
app = Flask(__name__)

# Used for sessions, flash messages, login cookies
load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# SQLite database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///news_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)


# =========================
# LOGIN MANAGER SETUP
# =========================
login_manager = LoginManager(app)

# Redirect unauthenticated users here
login_manager.login_view = "login"

# Disable default login message
login_manager.login_message = None


# =========================
# SUPPORTED NEWS CATEGORIES
# =========================
NICHES = [
    "Technology",
    "Finance",
    "Sports",
    "Politics",
    "Entertainment",
    "Health",
]


# =========================
# USER LOADER (Flask-Login)
# =========================
@login_manager.user_loader
def load_user(user_id):
    """
    Given a user_id from session, return the User object.
    Required by Flask-Login.
    """
    return db.session.get(User, int(user_id))


# =========================
# CONTEXT PROCESSOR
# =========================
@app.context_processor
def inject_fake_result():
    """
    Makes fake news verification result available
    in all templates automatically.
    """
    result = session.pop("fake_result", None)
    return dict(fake_result=result)


# =========================
# AUTHENTICATION ROUTES
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles new user registration.
    """
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validate input
        if not phone or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        # Check for existing user
        exists = User.query.filter(
            (User.email == email) | (User.phone == phone)
        ).first()

        if exists:
            flash("Phone or email already registered.", "danger")
            return redirect(url_for("register"))

        # Create new user with hashed password
        user = User(
            phone=phone,
            email=email,
            password_hash=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Validate credentials
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        # Login user and start session
        login_user(user)
        return redirect(url_for("news_list"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """
    Logs out the current user.
    """
    logout_user()
    return redirect(url_for("login"))


# =========================
# NEWS LIST & PREFERENCES
# =========================
@app.route("/")
@app.route("/news", methods=["GET", "POST"])
@login_required
def news_list():
    """
    Displays news based on user preferences.
    Allows updating preferred niches.
    """

    # Get current user's preferred niches
    user_niches = [p.niche for p in current_user.preferences]

    # Handle niche preference update
    if request.method == "POST":
        selected = request.form.getlist("niches")

        # Only upper limit enforced
        if len(selected) > 6:
            flash("You can select up to 6 niches only.", "warning")
            return redirect(url_for("news_list"))

        # Remove old preferences
        UserPreference.query.filter_by(
            user_id=current_user.id
        ).delete()

        # Add new preferences
        for niche in selected:
            db.session.add(
                UserPreference(user_id=current_user.id, niche=niche)
            )

        db.session.commit()
        flash("Preferences updated.", "success")

        user_niches = selected

    # Fetch latest news and cache into DB
    fetch_and_cache_news_for_user(db.session, user_niches)

    # Build news query
    query = News.query
    if user_niches:
        query = query.filter(News.niche.in_(user_niches))

    news_items = query.order_by(News.date.desc()).all()

    return render_template(
        "news_list.html",
        news_items=news_items,
        niches=NICHES,
        user_niches=set(user_niches),
        api_key_set=True,
    )


# =========================
# NEWS DETAIL & COMMENTS
# =========================
@app.route("/news/<int:news_id>", methods=["GET", "POST"])
@login_required
def news_detail(news_id):
    """
    Shows full news article and comments.
    Allows users to post comments.
    """

    news_item = News.query.get_or_404(news_id)

    # Handle comment submission
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        is_public = request.form.get("is_public") == "on"

        if content:
            db.session.add(
                Comment(
                    content=content,
                    is_public=is_public,
                    user_id=current_user.id,
                    news_id=news_id,
                )
            )
            db.session.commit()

        return redirect(
            url_for("news_detail", news_id=news_id) + "#comments"
        )

    # Fetch public comments + user's private comments
    comments = (
        Comment.query.filter(
            Comment.news_id == news_id,
            (Comment.is_public == True)
            | (
                (Comment.is_public == False)
                & (Comment.user_id == current_user.id)
            ),
        )
        .order_by(Comment.created_at.desc())
        .all()
    )

    return render_template(
        "news_detail.html",
        news_item=news_item,
        comments=comments,
    )


# =========================
# AI REALTIME NEWS BOT
# =========================
@app.route("/ai-bot", methods=["GET", "POST"])
@login_required
def ai_bot():
    """
    Allows users to search live news using AI.
    """
    results = None

    if request.method == "POST":
        keywords = request.form.get("info", "").strip()
        date_str = request.form.get("date", "").strip() or None
        year_str = request.form.get("year", "").strip()
        niche = request.form.get("niche", "").strip() or None

        year = int(year_str) if year_str else None

        results = ai_realtime_news(
            keywords=keywords,
            niche=niche,
            date_str=date_str,
            year=year,
            country="us",
            page_size=10,
            debug=False,
        )

    return render_template(
        "ai_bot.html",
        results=results,
        scroll_to_results=True,
    )


# =========================
# FAKE NEWS VERIFICATION
# =========================
@app.route("/verify-news", methods=["POST"])
@login_required
def verify_news():
    """
    Uses Perplexity AI to fact-check pasted news text.
    """
    text = request.form.get("news_text", "").strip()

    if not text:
        flash("Paste some news text first.", "warning")
        return redirect(request.referrer or url_for("news_list"))

    # AI-based verification
    result = classify_news_transformer(text)

    # Store result in session for template access
    session["fake_result"] = result

    return redirect(request.referrer or url_for("news_list"))


# =========================
# APP START
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True,
           use_reloader=False)
