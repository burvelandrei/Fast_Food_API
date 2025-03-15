from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from db.connect import get_session
from schemas.order import OrderOut, DeliveryCreate, OrderStatus
from schemas.user import UserOut
from schemas.cart import CartItemCreate
from db.operations import OrderDO
from utils.redis_connect import get_redis
from utils.cache_manager import request_key_builder
from services.redis_cart import get_cart, remove_cart, repeat_item_to_cart
from services.auth import get_current_user


router = APIRouter(prefix="/orders", tags=["Orders"])


# Роутер для подтверждения заказа пользователя
@router.post("/confirmation/")
async def confirmation_order(
    delivery_data: DeliveryCreate,
    user: UserOut = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    cart = await get_cart(
        user_id=user.id,
        redis=redis,
        session=session,
    )
    if cart and cart.cart_items:
        await OrderDO.add(
            user_id=user.id,
            session=session,
            values=cart,
            delivery_data=delivery_data,
        )
        await remove_cart(
            user_id=user.id,
            redis=redis,
        )
        return JSONResponse(
            content={"message": "Order successfully created"},
            status_code=201,
        )
    return HTTPException(
        status_code=400,
        detail="No products in cart",
    )


# Роутер получения всех заказов пользователя (если указан status только заказы по статусу)
@router.get("/", response_model=list[OrderOut])
@cache(expire=30, key_builder=request_key_builder)
async def get_all_orders(
    status: str = Query(None),
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not status:
        orders = await OrderDO.get_all(user_id=user.id, session=session)
    else:
        orders = await OrderDO.get_all_by_status(
            user_id=user.id,
            status=status,
            session=session,
        )
    return orders


# Получение выполненных заказов
@router.get("/history/", response_model=list[OrderOut])
@cache(expire=30, key_builder=request_key_builder)
async def get_order_history(
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    orders = await OrderDO.get_all_by_status(
        user_id=user.id,
        status=OrderStatus.COMPLETED.value,
        session=session,
    )
    return orders


# Получение всех заказов, кроме выполненных (текущие заказы)
@router.get("/current/", response_model=list[OrderOut])
@cache(expire=30, key_builder=request_key_builder)
async def get_current_orders(
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    statuses = [
        status.value for status in OrderStatus if status != OrderStatus.COMPLETED
    ]
    orders = await OrderDO.get_all_by_statuses(
        user_id=user.id,
        statuses=statuses,
        session=session,
    )
    return orders


# Роутер получения заказа пользователя
@router.get("/{order_id}/", response_model=OrderOut)
@cache(expire=30, key_builder=request_key_builder)
async def get_order(
    order_id: int,
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    order = await OrderDO.get_by_id(
        order_id=order_id,
        user_id=user.id,
        session=session,
    )
    return order


# Роутер повторения заказа (добавляет в корзину те же продукты из заказа по id)
@router.post("/repeat/{order_id}/")
async def repeat_order_to_cart(
    order_id: int,
    user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    # чистим корзину перед добавлением товаров из заказа
    cart = await get_cart(
        user_id=user.id,
        redis=redis,
        session=session,
    )
    if cart and cart.cart_items:
        await remove_cart(user.id, redis)
    db_order = await OrderDO.get_by_id(
        order_id=order_id,
        user_id=user.id,
        session=session,
    )
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    for order_item in db_order.order_items:
        cart_item = CartItemCreate(
            product_id=order_item.product_id,
            size_id=order_item.size_id,
            quantity=order_item.quantity,
        )
        await repeat_item_to_cart(
            cart_item=cart_item,
            user_id=user.id,
            redis=redis,
            session=session,
        )

    return JSONResponse(
        content={"message": "Products from the order have been added to the cart"},
        status_code=200,
    )
