"""Server configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Order Block"
    app_version: str = "2.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = Path.home() / ".order-block"
    thumbnail_sizes: dict = {"thumb": 200, "medium": 600}

    model_config = {"env_prefix": "ORDER_BLOCK_"}


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
