import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
from starlette.responses import JSONResponse

from common import AppConfig, application_init
from common.telemetry import instrument_third_party
from http_app.routes import init_routes

# These instrumentors patch and wrap libraries, we want
# to execute them ASAP
instrument_third_party()


def create_app(
    test_config: AppConfig | None = None,
) -> FastAPI:
    app_config = test_config or AppConfig()

    application_init(app_config)

    app = FastAPI(
        debug=app_config.DEBUG,
        title=app_config.APP_NAME,
    )
    init_exception_handlers(app)

    if app_config.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_config.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=app_config.CORS_METHODS,
            allow_headers=app_config.CORS_HEADERS,
        )

    init_routes(app)
    FastAPIInstrumentor.instrument_app(app)

    return app


def init_exception_handlers(app: FastAPI) -> None:
    # This is a catch-all middleware for unhandled exceptions
    # other Exception handlers should be initialised using
    # the @app.exception_handler decorator
    # https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
    @app.middleware("http")
    async def add_exception_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logging.exception(e)
            return JSONResponse({"error": "Internal server error"}, status_code=500)
