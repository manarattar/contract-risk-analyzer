"""Version 2: legacy unauthenticated routes are intentionally not mounted."""
from app.review.application import app

__all__ = ["app"]
