from time import time

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import __version__
from app.config import get_settings
from app.db import init_db
from app.logging_config import setup_logging
from app.metrics import REQUEST_ERRORS, REQUEST_LATENCY
from app.routers import router as entries_router


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    init_db()

    app = FastAPI(title=settings.app_name, version=__version__)
    app.include_router(entries_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time()
        try:
            response: Response = await call_next(request)
            return response
        except Exception as exc:  # pragma: no cover
            REQUEST_ERRORS.labels(request.method, request.url.path, 500).inc()
            raise exc
        finally:
            duration = time() - start
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)

    log = structlog.get_logger()

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        response = await call_next(request)
        log.info(
            "request_complete",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        if response.status_code >= 500:
            REQUEST_ERRORS.labels(request.method, request.url.path, response.status_code).inc()
        return response

    @app.get("/health", tags=["monitoring"])
    async def health():
        return {"status": "ok"}

    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
