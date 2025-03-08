from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.order import OrderOut
from schemas.user import UserOut
from db.operations import OrderDO
from utils.redis_connect import get_redis
from services.redis_cart import get_cart, remove_cart
from services.auth import get_current_user


router = APIRouter(prefix="/orders", tags=["Orders"])


# Роутер для подтверждения заказа пользователя
@router.post("/confirmation/")
async def confirmation_order(
    user: UserOut = Depends(get_current_user),
    redis=Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    cart = await get_cart(user.id, redis, session)
    if cart and cart.cart_items:
        await OrderDO.add(user_id=user.id, session=session, values=cart)
        await remove_cart(user.id, redis)
        return JSONResponse(
            content={"message": "Order successfully created"},
            status_code=201,
        )
    return HTTPException(
        status_code=400,
        detail="No products in cart",
    )


# Роутер получения всех заказов пользователя
@router.get("/", response_model=list[OrderOut])
async def get_all_order(
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    orders = await OrderDO.get_all(user.id, session)
    return orders
