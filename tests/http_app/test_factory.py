import pytest
from starlette.middleware.cors import CORSMiddleware

from http_app import create_app
from src.common.config import AppConfig


def test_with_default_config() -> None:
    app = create_app()
    assert app.debug is False


def test_with_debug_config() -> None:
    app = create_app(
        test_config=AppConfig(
            ENVIRONMENT="test",
            DEBUG=True,
        )
    )

    assert app.debug is True


@pytest.mark.parametrize(
    ["origins", "middleware_present"],
    (
        pytest.param(["*"], True),
        pytest.param([], False),
    ),
)
def test_cors_middleware_added_if_origins_provided(origins: list, middleware_present: bool) -> None:
    app = create_app(
        test_config=AppConfig(
            CORS_ORIGINS=origins,
        )
    )

    assert bool([x for x in app.user_middleware if x.cls is CORSMiddleware]) == middleware_present
