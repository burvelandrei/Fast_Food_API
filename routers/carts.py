from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.cart import CartItemModify
from schemas.user import UserOut
from db.connect import get_session
from utils.redis_connect import get_redis
from services.redis_cart import (
    add_to_cart,
    get_cart,
    get_cart_item,
    remove_item,
    remove_cart,
    update_cart_item,
)
from services.auth import get_current_user
from fastapi_cache.decorator import cache


router = APIRouter(prefix="/carts", tags=["Carts"])


# Роутер добавления продукта в корзину
@router.post("/add/{product_id}/")
async def add_item_to_cart(
    product_id: int,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    await add_to_cart(user.id, product_id, redis, session)
    return JSONResponse(
        content={"message": "Product added to cart"},
        status_code=201,
    )


# Роутер изменения количества продукта в корзине
@router.patch("/update/{product_id}/")
async def update_item_to_cart(
    product_id: int,
    item_parametrs: CartItemModify,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    await update_cart_item(
        product_id,
        user.id,
        item_parametrs.quantity,
        redis,
        session,
    )
    return JSONResponse(
        content={"message": "Product quantity updated"},
        status_code=200,
    )


# Роутер получения корзины пользователя
@router.get("/")
@cache(expire=10)
async def get_cart_user(
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    return await get_cart(user.id, redis, session)


# Роутер получения продукта из корзины пользователя
@router.get("/{product_id}/")
@cache(expire=10)
async def get_cart_item_user(
    product_id: int,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    return await get_cart_item(product_id, user.id, redis, session)


# Роутер удаления продутка из корзины
@router.delete("/{product_id}/")
async def delete_item_from_cart(
    product_id: int,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
):
    await remove_item(user.id, product_id, redis)
    return JSONResponse(
        content={"message": "Product removed from cart"},
        status_code=200,
    )


# Роутер очистки корзины
@router.delete("/")
async def delete_cart(
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
):
    await remove_cart(user.id, redis)
    return JSONResponse(
        content={"message": "Cart successfully removed"},
        status_code=200,
    )
