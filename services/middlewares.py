import logging
import logging.config
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from services.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("fastapi")

async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception {exc.status_code}: {exc.detail} | Path: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(status_code=400, content={"detail": "Validation error"})

async def global_exception_handler(request: Request, exc: Exception):
    logger.critical(f"Unhandled Exception: {str(exc)} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})



class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"{request.method} Path: {request.url.path}")
        response = await call_next(request)
        return response