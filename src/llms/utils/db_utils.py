import time
import sqlite3
from functools import wraps

def retry_on_lock(max_retries=3, delay=0.1):
    """Decorator to retry database operations on lock errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    raise
            return func(*args, **kwargs)
        return wrapper
    return decorator