import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from routers import products, category, users, carts, orders
from admin.view import setup_admin
from utils.middlewares import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
    LogRequestsMiddleware,
)
from utils.cache_manager import lifespan


app = FastAPI(title="FastFood API", lifespan=lifespan)
# Подключение миддлвари и обработчиков ошибок для логов
app.add_middleware(LogRequestsMiddleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
# Подключение админки и рутов
setup_admin(app)
app.include_router(products.router)
app.include_router(category.router)
app.include_router(users.router)
app.include_router(carts.router)
app.include_router(orders.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
