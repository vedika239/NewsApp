# Used to make HTTP requests to the NewsAPI
import requests

# Used to handle dates and timestamps
from datetime import datetime

# Used for type hints (improves readability and IDE support)
from typing import Optional, List, Dict, Any


# =========================
# API CONFIGURATION
# =========================

# Hard-coded NewsAPI key (kept exactly as requested)
NEWS_API_KEY = "18433ff920554a31bd4a72976a0a2e6a"

# NewsAPI endpoints
TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"


# =========================
# NICHE MAPPINGS
# =========================

# Maps user-friendly niches to NewsAPI categories
NICHE_TO_CATEGORY = {
    "Technology": "technology",
    "Finance": "business",
    "Sports": "sports",
    "Politics": "general",
    "Entertainment": "entertainment",
    "Health": "health"
}

# Expanded keyword queries to improve search accuracy
# Used mainly for the "everything" endpoint
NICHE_TO_Q = {
    "Technology": "technology OR AI OR startup OR software",
    "Finance": "finance OR market OR economy OR stocks",
    "Sports": "sports OR cricket OR football",
    "Politics": "politics OR government OR election",
    "Entertainment": "entertainment OR film OR bollywood OR music",
    "Health": "health"
}


# =========================
# SAFE API CALL HELPER
# =========================
def _safe_get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Makes a GET request to the given URL and safely returns JSON.
    Adds HTTP status code to the response for debugging.
    """

    # Send request to NewsAPI
    r = requests.get(url, params=params, timeout=12)

    try:
        # Try parsing JSON response
        data = r.json()
    except Exception:
        # If parsing fails, return empty dict
        data = {}

    # Attach HTTP status code for debugging purposes
    data["_http_status"] = r.status_code
    return data


# =========================
# MAIN AI NEWS FUNCTION
# =========================
def ai_realtime_news(
    keywords: str,                  # Search keywords entered by user
    niche: Optional[str] = None,    # Optional niche/category
    date_str: Optional[str] = None, # Specific date (YYYY-MM-DD)
    year: Optional[int] = None,     # Specific year
    country: str = "us",            # Country filter (default US)
    page_size: int = 10,            # Number of articles to return
    debug: bool = True,             # Enable debug logs
) -> List[Dict[str, Any]]:
    """
    REAL-TIME AI NEWS SEARCH FLOW:

    1️⃣ Try TOP HEADLINES (most recent, live news)
    2️⃣ If no results → fallback to EVERYTHING (broader historical search)

    Returns a clean list of articles:
    title, description, url, publishedAt, source
    """

    # Clean up keyword input
    keywords = (keywords or "").strip()

    # If no keywords provided, return empty list
    if not keywords:
        return []

    # Resolve category and expanded query terms
    category = NICHE_TO_CATEGORY.get(niche or "", None)
    q_boost = NICHE_TO_Q.get(niche or "", "")

    # Combine user keywords with niche-based expansion
    q = f"({keywords})" if not q_boost else f"({keywords}) AND ({q_boost})"


    # =========================
    # A) TOP HEADLINES (LIVE)
    # =========================
    th_params = {
        "apiKey": NEWS_API_KEY,
        "country": country,
        "pageSize": page_size,
        "q": keywords,     # Keywords allowed in top-headlines
    }

    # Add category only if available
    if category:
        th_params["category"] = category

    # Call the API safely
    th_data = _safe_get(TOP_HEADLINES_URL, th_params)
    th_articles = th_data.get("articles") or []

    # Debug logging
    if debug:
        print(
            "AI DEBUG | top-headlines http:",
            th_data.get("_http_status"),
            "status:", th_data.get("status"),
            "totalResults:", th_data.get("totalResults"),
            "category:", category,
            "q:", keywords
        )

    # If live headlines are found, return them immediately
    if th_data.get("status") == "ok" and len(th_articles) > 0:
        return _clean_articles(th_articles)


    # =========================
    # B) EVERYTHING (FALLBACK)
    # =========================
    ev_params = {
        "apiKey": NEWS_API_KEY,
        "q": q,                   # Expanded query
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": page_size,
    }

    # Apply date filter if provided
    if date_str:
        ev_params["from"] = date_str
        ev_params["to"] = date_str

    # Apply year filter if provided
    elif year:
        ev_params["from"] = f"{year}-01-01"
        ev_params["to"] = f"{year}-12-31"

    # Call the EVERYTHING endpoint
    ev_data = _safe_get(EVERYTHING_URL, ev_params)
    ev_articles = ev_data.get("articles") or []

    # Debug logging
    if debug:
        print(
            "AI DEBUG | everything http:",
            ev_data.get("_http_status"),
            "status:", ev_data.get("status"),
            "totalResults:", ev_data.get("totalResults"),
            "q:", q,
            "from:", ev_params.get("from"),
            "to:", ev_params.get("to")
        )

    # If fallback search finds results, return them
    if ev_data.get("status") == "ok" and len(ev_articles) > 0:
        return _clean_articles(ev_articles)

    # If nothing found, return empty list
    return []


# =========================
# CLEAN & NORMALIZE RESULTS
# =========================
def _clean_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans raw NewsAPI articles into a consistent format
    suitable for templates or API responses.
    """

    cleaned = []

    for a in articles:
        title = a.get("title") or ""
        desc = a.get("description") or a.get("content") or ""
        url = a.get("url")

        # Extract date only (YYYY-MM-DD)
        pub = a.get("publishedAt", "")[:10]

        # Extract source name safely
        source = (a.get("source") or {}).get("name") or "Unknown"

        # Skip invalid articles
        if not title or not url:
            continue

        # Append cleaned article
        cleaned.append({
            "title": title.strip(),
            "description": desc.strip(),
            "url": url,
            "publishedAt": pub,
            "source": source,
        })

    return cleaned
