import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import products, category, users, carts, orders
from admin.view import setup_admin


app = FastAPI(title="FastFood API")
setup_admin(app)
app.include_router(products.router)
app.include_router(category.router)
app.include_router(users.router)
app.include_router(carts.router)
app.include_router(orders.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)