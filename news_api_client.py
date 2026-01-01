# Import datetime utilities to handle date conversion
from datetime import datetime, date
import os
# Used for type hinting (better readability and editor support)
from typing import List, Optional

# Requests library is used to make HTTP calls to the News API
import requests

# Import the News database model to store fetched news
from models import News


# =========================
# NEWS API CONFIGURATION
# =========================

# HARD-CODED API KEY (as requested)
# This key authenticates requests to the News API
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Endpoint for fetching top headlines
TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"

# Mapping user-friendly niches to NewsAPI categories
NICHE_TO_CATEGORY = {
    "Technology": "technology",
    "Finance": "business",
    "Sports": "sports",
    "Politics": "general",
    "Entertainment": "entertainment",
}


# =========================
# HELPER FUNCTION
# =========================
def _parse_date(published_at: Optional[str]) -> date:
    """
    Converts the publishedAt string from News API into a Python date object.
    If conversion fails, today's date is used as a fallback.
    """

    # If no date is provided, return today's date
    if not published_at:
        return date.today()

    try:
        # Convert ISO timestamp (e.g., 2024-01-01T10:30:00Z) to datetime
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

        # Return only the date part
        return dt.date()

    except Exception:
        # If parsing fails, default to today's date
        return date.today()


# =========================
# MAIN FUNCTION
# =========================
def fetch_and_cache_news_for_user(
    db_session,               # Active database session
    niches: List[str],        # List of user-selected niches
    country: str = "us",      # Country code (US forced for reliability)
    page_size: int = 20,      # Number of articles per request
):
    """
    Fetches news articles from News API based on user niches
    and stores them in the database while avoiding duplicates.
    """

    # Debug logs to verify API key and niches being used
    print("DEBUG | Using NEWS_API_KEY:", NEWS_API_KEY)
    print("DEBUG | Fetching news for niches:", niches)

    # If user has no preferences, default to Technology
    if not niches:
        niches = ["Technology"]

    # Loop through each user-selected niche
    for niche in niches:
        # Convert niche into API-supported category
        category = NICHE_TO_CATEGORY.get(niche, "general")

        # Parameters sent to the News API
        params = {
            "apiKey": NEWS_API_KEY,
            "country": country,
            "category": category,
            "pageSize": page_size,
        }

        # Debug: print request parameters
        print("DEBUG | Request params:", params)

        # Make the API request
        response = requests.get(
            TOP_HEADLINES_URL,
            params=params,
            timeout=10
        )

        # Debug: print HTTP response status
        print("DEBUG | HTTP status:", response.status_code)

        # Parse JSON response
        data = response.json()

        # Extract list of articles from response
        articles = data.get("articles", [])

        # Debug: print number of articles fetched
        print(f"DEBUG | {niche} articles fetched:", len(articles))

        # Loop through each article
        for art in articles:
            # Extract article URL (used to prevent duplicates)
            url = art.get("url")

            # Skip articles without a valid URL
            if not url:
                continue

            # Extract article fields with safe fallbacks
            title = art.get("title") or "Untitled"
            description = art.get("description") or ""
            content = art.get("content") or description

            # Convert published date to Python date
            published = _parse_date(art.get("publishedAt"))

            # Check if article already exists in database
            existing = db_session.query(News).filter_by(
                source_url=url
            ).first()

            # Skip duplicates
            if existing:
                continue

            # Create new News object
            news = News(
                title=title,
                content=content,
                niche=niche,
                date=published,
                source_url=url,
            )

            # Add news to database session
            db_session.add(news)

        # Commit all added articles to the database
        db_session.commit()
