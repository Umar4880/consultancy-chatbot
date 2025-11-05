class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Error connecting to database"""
    pass

class DatabaseLockError(DatabaseError):
    """Database is locked"""
    pass

class DatabaseQueryError(DatabaseError):
    """Error executing database query"""
    pass