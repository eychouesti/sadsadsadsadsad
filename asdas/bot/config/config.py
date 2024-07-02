from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    API_ID: int
    API_HASH: str
    API_BASE_URL: str = "https://drumapi.wigwam.app/api"

    CLAIM_FARM_INTERVAL: int = 4 * 60 * 60  
    TAP_INTERVAL: int = 60  
    USE_PROXY: bool = False
    PROXY_URL: str | None = None  # Değişiklik burada

settings = Settings()
