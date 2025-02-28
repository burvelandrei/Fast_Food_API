from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.cart import CartItemCreate
from schemas.user import UserOut
from db.connect import get_session
from dependencies import get_redis
from services.redis_cart import add_to_cart, get_cart, remove_item
from services.auth import get_current_user


router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post("/add")
async def add_item_to_cart(
    item: CartItemCreate,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    return await add_to_cart(user.id, item, redis, session)


@router.get("/")
async def get_cart_user(
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    return await get_cart(user.id, redis, session)


@router.delete("/{product_id}")
async def delete_item_from_cart(
    product_id: int,
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
):
    return await remove_item(user.id, product_id, redis)
