import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager

class DatabaseConfig:
    """Centralized database configuration"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use environment variable or default to project root
            db_path = os.getenv('CHAT_DB_PATH', 'chat_history.db')
        
        self.db_path = Path(db_path)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Create directory for database if it doesn't exist"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()