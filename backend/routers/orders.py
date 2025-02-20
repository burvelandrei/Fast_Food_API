from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.order import OrderOut
from db.operations import OrderDO, OrderItemDO
from dependencies import verify_api_key, get_redis
from services.redis_cart import get_cart, remove_cart


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/{user_id}")
async def confirmation_order(
    user_id: int,
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    cart = await get_cart(user_id, redis)
    if cart:
        await OrderDO.add(user_id=user_id, session=session, values=cart)
        await remove_cart(user_id, redis)
        return {"message": "Order add"}
    return {"message": "No products in cart"}


@router.get("/{user_id}", response_model=list[OrderOut])
async def get_all_order(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
):
    orders = await OrderDO.get_all(user_id, session)
    return orders