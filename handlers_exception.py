import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("fastapi")

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception {exc.status_code}: {exc.detail} | Path: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(status_code=400, content={"detail": "Validation error"})

async def global_exception_handler(request: Request, exc: Exception):
    logger.critical(f"Unhandled Exception: {str(exc)} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})