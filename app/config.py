from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Car Price Prediction API"
    api_version: str = "v1"
    model_path: str = "models/car_price_model.pkl"
    cors_origins: list[str] = ["*"]  # tighten to your frontend's origin in production

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
