from collections.abc import Iterator

import pytest
from fastapi import FastAPI

from http_app import create_app


@pytest.fixture(scope="session")
def testapp(test_config) -> Iterator[FastAPI]:
    app = create_app(test_config=test_config)
    yield app
