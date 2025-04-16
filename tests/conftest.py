import pytest

from src.common import AppConfig


@pytest.fixture(autouse=True)
def anyio_backend():
    """
    For now, we don't have reason to test anything but asyncio
    https://anyio.readthedocs.io/en/stable/testing.html
    """
    return "asyncio"


@pytest.fixture(scope="session")
def test_config() -> AppConfig:
    return AppConfig(ENVIRONMENT="test", CORS_ORIGINS=["*"])
