# Flask-SQLAlchemy is used to interact with the database using Python classes
from flask_sqlalchemy import SQLAlchemy

# UserMixin provides default implementations for Flask-Login
# (like is_authenticated, is_active, get_id, etc.)
from flask_login import UserMixin

# Used to automatically store timestamps (e.g., comment creation time)
from datetime import datetime

# Create the database instance
db = SQLAlchemy()


# =========================
# USER MODEL
# =========================
class User(db.Model, UserMixin):
    """
    Represents an application user.
    Handles authentication and user-related data.
    """
    __tablename__ = "user"

    # Primary key (unique ID for each user)
    id = db.Column(db.Integer, primary_key=True)

    # User phone number (must be unique)
    phone = db.Column(db.String(20), nullable=False, unique=True)

    # User email address (must be unique)
    email = db.Column(db.String(120), nullable=False, unique=True)

    # Hashed password (never store plain text passwords)
    password_hash = db.Column(db.String(256), nullable=False)

    # One-to-many relationship:
    # One user can have multiple preferences (niches)
    preferences = db.relationship(
        "UserPreference",
        backref="user",                 # Allows preference.user access
        cascade="all, delete-orphan",   # Deletes preferences if user is deleted
        lazy=True
    )

    # One-to-many relationship:
    # One user can post multiple comments
    comments = db.relationship(
        "Comment",
        backref="user",                 # Allows comment.user access
        cascade="all, delete-orphan",
        lazy=True
    )


# =========================
# USER PREFERENCES (NICHES)
# =========================
class UserPreference(db.Model):
    """
    Stores user interests (e.g., politics, sports, tech).
    """
    __tablename__ = "user_preference"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # News category the user is interested in
    niche = db.Column(db.String(50), nullable=False, index=True)

    # Foreign key linking preference to a user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


# =========================
# NEWS MODEL
# =========================
class News(db.Model):
    """
    Represents a news article stored in the database.
    """
    __tablename__ = "news"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # News headline/title
    title = db.Column(db.String(250), nullable=False)

    # Full news content/body
    content = db.Column(db.Text, nullable=False)

    # Category of the news (e.g., sports, politics)
    niche = db.Column(db.String(50), nullable=False, index=True)

    # Date the news was published
    date = db.Column(db.Date, nullable=False, index=True)

    # URL of the news source
    # Used to prevent duplicate entries when fetching from APIs
    source_url = db.Column(db.String(400), unique=True, nullable=True)

    # One-to-many relationship:
    # One news article can have multiple comments
    comments = db.relationship(
        "Comment",
        backref="news",                 # Allows comment.news access
        cascade="all, delete-orphan",
        lazy=True
    )


# =========================
# COMMENTS MODEL
# =========================
class Comment(db.Model):
    """
    Stores user comments on news articles.
    """
    __tablename__ = "comment"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Comment text/content
    content = db.Column(db.Text, nullable=False)

    # Determines whether comment is visible to others
    is_public = db.Column(db.Boolean, default=True)

    # Timestamp when comment was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key linking comment to a user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Foreign key linking comment to a news article
    news_id = db.Column(
        db.Integer,
        db.ForeignKey("news.id"),
        nullable=False
    )
