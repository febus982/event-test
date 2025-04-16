from .config import AppConfig
from .logs import init_logger
from .telemetry import instrument_opentelemetry


def application_init(
    app_config: AppConfig,
) -> None:
    init_logger(app_config)
    instrument_opentelemetry(app_config)
