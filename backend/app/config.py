from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    bot_token: str
    runpod_endpoint_id: str
    runpod_api_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()