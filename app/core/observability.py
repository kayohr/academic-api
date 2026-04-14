"""
Observabilidade: logs estruturados em JSON, middleware de tempo de resposta e rate limiting.
"""

import logging
import time
import uuid
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse


# ── Logs estruturados em JSON ─────────────────────────────────────────────────

def configurar_logs(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silencia logs verbosos de libs externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("academic_api")


# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "RATE_LIMIT_EXCEEDED", "message": "Muitas requisições. Tente novamente em instantes."},
        headers={"Retry-After": "60"},
    )


# ── Middleware de tempo de resposta ───────────────────────────────────────────

async def middleware_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    inicio = time.perf_counter()

    logger.info(
        "request_start",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
        },
    )

    response = await call_next(request)

    duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duracao_ms}ms"

    logger.info(
        "request_end",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duracao_ms,
        },
    )

    return response


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_observabilidade(app: FastAPI, log_level: str = "INFO") -> None:
    configurar_logs(log_level)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.middleware("http")(middleware_logging)

    logger.info("observabilidade_configurada", extra={"log_level": log_level})
