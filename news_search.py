# Import List and Optional for type hinting (helps with code readability and IDE support)
from typing import List, Optional

# Import date class to filter news by a specific date
from datetime import date

# Import SQLAlchemy helpers for complex queries
from sqlalchemy import or_, func, extract

# Import the News database model
from models import News


def search_news(
    db_session,                   # Active database session used to run queries
    query: str,                    # Search text entered by the user
    specific_date: Optional[date] = None,  # Filter news by exact date (optional)
    year: Optional[int] = None     # Filter news by year only (optional)
) -> List[News]:
    """
    Search news articles from the database based on text, date, or year.
    Returns a list of News objects.
    """

    # Start a base query selecting all rows from the News table
    q = db_session.query(News)

    # If a specific date is provided, filter news from that exact date
    if specific_date:
        q = q.filter(News.date == specific_date)

    # If a year is provided, filter news from that year only
    # extract("year", News.date) gets the year part from the date column
    if year:
        q = q.filter(extract("year", News.date) == year)

    # If a search query is provided
    if query:
        # Convert query to lowercase and add wildcards for partial matching
        like = f"%{query.lower()}%"

        # Filter news where the query appears in the title OR content
        # func.lower ensures case-insensitive search
        q = q.filter(
            or_(
                func.lower(News.title).like(like),
                func.lower(News.content).like(like)
            )
        )

    # Order results by date in descending order (latest news first)
    return q.order_by(News.date.desc()).all()
