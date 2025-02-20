import uvicorn
from fastapi import FastAPI
from routers import products, category, users, cart


app = FastAPI(title="FastFood API")
app.include_router(products.router)
app.include_router(category.router)
app.include_router(users.router)
app.include_router(cart.router)



if __name__=="__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)