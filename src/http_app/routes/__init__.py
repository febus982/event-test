from fastapi import FastAPI

from http_app.routes import (
    ping,
)


def init_routes(app: FastAPI) -> None:
    app.include_router(ping.router)
