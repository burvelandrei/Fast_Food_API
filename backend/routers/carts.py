from fastapi import APIRouter, Depends
from schemas.cart import CartItemCreate
from dependencies import get_redis, verify_api_key
from services.redis_cart import add_to_cart, get_cart, get_cart_item, remove_item


router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post("/{user_id}/add")
async def add_item_to_cart(
    user_id: int,
    item: CartItemCreate,
    redis=Depends(get_redis),
    api_key: str = Depends(verify_api_key),
):
    return await add_to_cart(user_id, item, redis)


@router.get("/{user_id}")
async def get_cart_user(
    user_id: int, redis=Depends(get_redis), api_key: str = Depends(verify_api_key)
):
    return await get_cart(user_id, redis)


@router.get("/{user_id}/{product_id}")
async def get_cart_item_user(
    user_id: int,
    product_id: int,
    redis=Depends(get_redis),
    api_key: str = Depends(verify_api_key),
):
    return await get_cart_item(user_id, product_id, redis)


@router.delete("/{user_id}/{product_id}")
async def delete_item_from_cart(
    user_id: int,
    product_id: int,
    redis=Depends(get_redis),
    api_key: str = Depends(verify_api_key),
):
    return await remove_item(user_id, product_id, redis)

