import uuid

def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def generate_user_id() -> str:
    """Generate a unique user ID."""
    return str(uuid.uuid4())
