from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

TYPE_ENVIRONMENT = Literal["local", "test", "staging", "production"]


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    APP_NAME: str = "bootstrap"
    CORS_ORIGINS: list[str] = Field(default_factory=list)
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    DEBUG: bool = False
    ENVIRONMENT: TYPE_ENVIRONMENT = "local"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_LOGS_ENDPOINT: Optional[str] = None
