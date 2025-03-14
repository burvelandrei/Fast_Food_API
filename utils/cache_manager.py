from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from utils.redis_connect import get_redis_no_decode
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_client = await get_redis_no_decode()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield


def request_key_builder(
    func,
    namespace: str = "",
    request: Request = None,
    response: Response = None,
    *args,
    **kwargs,
):
    return ":".join(
        [
            namespace,
            request.method.lower(),
            request.url.path,
            repr(sorted(request.query_params.items())),
        ]
    )
