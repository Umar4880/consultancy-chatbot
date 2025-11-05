from src.llms.model import ModelManagement

def get_model():
    """Dependency to get model instance"""
    return ModelManagement()
