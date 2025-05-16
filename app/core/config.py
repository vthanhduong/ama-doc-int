from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AZURE_RESOURCE_API_KEY: str
    AZURE_RESOURCE_ENDPOINT: str
    APP_NAME: str
    API_VERSION: str
    model_config = SettingsConfigDict(env_file='.env')
    
settings = Settings()