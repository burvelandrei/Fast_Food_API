from fastapi import APIRouter, Depends
from schemas.cart import CartItemCreate
from schemas.user import UserOut
from dependencies import get_redis
from services.redis_cart import add_to_cart, get_cart, get_cart_item, remove_item
from services.auth import get_current_user


router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post("/add")
async def add_item_to_cart(
    item: CartItemCreate,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
):
    return await add_to_cart(user.id, item, redis)


@router.get("/{user_id}")
async def get_cart_user(
    user_id: int, redis=Depends(get_redis)
):
    return await get_cart(user_id, redis)


@router.get("/{user_id}/{product_id}")
async def get_cart_item_user(
    user_id: int,
    product_id: int,
    redis=Depends(get_redis),
):
    return await get_cart_item(user_id, product_id, redis)


@router.delete("/{user_id}/{product_id}")
async def delete_item_from_cart(
    user_id: int,
    product_id: int,
    redis=Depends(get_redis),
):
    return await remove_item(user_id, product_id, redis)
