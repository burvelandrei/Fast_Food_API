import uvicorn
from fastapi import FastAPI
from backend.routers import products
from routers import category


app = FastAPI(title="FastFood API")
app.include_router(products.router)
app.include_router(category.router)



if __name__=="__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)