from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables first - use absolute path to be sure
env_path = Path(r"C:\Users\ranau\OneDrive\Desktop\genaipractice\fewshort_consultancy_cahtboat\.env")
print(f"DEBUG: Looking for .env file at: {env_path}")
print(f"DEBUG: .env file exists: {env_path.exists()}")
load_dotenv(dotenv_path=env_path)


class ChatModelSetting(BaseSettings):

    model: str = Field('gemini-2.0-flash', env="MODEL_NAME")
    temperature: float = Field(1.0, env="TEMPERATURE")
    api_key: str = Field("AIzaSyBcdqi4JYHrXxLhYafOoA-lCDnDaGC7Rlg", env="GOOGLE_API_KEY")  # Direct hardcode
    max_tokens: int = Field(512, env="MAX_TOKENS")

    app_name: str = "Nova Consultant"
    log_level: str = Field("INFO", env="LOG_LEVEL")
    debug: bool = Field(False, env="DEBUG")

    # memory_type: str = "hybrid"  # Buffer + Summary
    # buffer_memory_size: int = Field(15, env="BUFFER_MEMORY_SIZE")  # Last 15 messages
    # summary_memory_enabled: bool = Field(True, env="SUMMARY_MEMORY_ENABLED")
    # summary_trigger_threshold: int = Field(10, env="SUMMARY_TRIGGER")  # When to create summary
    
    class Config:
        env_file = str(env_path)
        case_sensitive = False
        extra = "allow"


config = ChatModelSetting()

# Debug the actual loaded values
print(f"DEBUG CONFIG: api_key = {config.api_key}")
print(f"DEBUG CONFIG: model = {config.model}")
print(f"DEBUG CONFIG: temperature = {config.temperature}")