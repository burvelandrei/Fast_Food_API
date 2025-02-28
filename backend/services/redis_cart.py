import json
from redis.asyncio import Redis
from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from db.operations import ProductDO
from schemas.cart import CartItemCreate, CartItemOut, CartOut
from schemas.product import ProductOut


async def add_to_cart(
    user_id: int,
    cart_item: CartItemCreate,
    redis: Redis,
    session: AsyncSession,
):
    product = await ProductDO.get_by_id(session=session, id=cart_item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    cart_key = f"cart_{user_id}"
    existing_item = await redis.hget(cart_key, str(cart_item.product_id))

    if existing_item:
        existing_item = json.loads(existing_item)
        existing_item["quantity"] = cart_item.quantity
    else:
        existing_item = cart_item.dict()
    await redis.hset(cart_key, str(cart_item.product_id), json.dumps(existing_item))
    if not await redis.exists(cart_key):
        await redis.expire(cart_key, 24 * 60 * 60)
    return Response(content="Product added to cart", status_code=201)


async def get_cart(
    user_id: int,
    redis: Redis,
    session: AsyncSession,
):
    cart_key = f"cart_{user_id}"
    cart_items = await redis.hgetall(cart_key)

    if not cart_items:
        return CartOut(
            user_id=user_id,
            items=[],
            total_amount=0,
        )
    items = []
    total_amount = 0
    for product_id, item_data in cart_items.items():
        item = json.loads(item_data)
        product = await ProductDO.get_by_id(session=session, id=int(product_id))
        if not product:
            continue
        product = ProductOut(**product.__dict__)
        total_price = product.final_price * int(item["quantity"])
        total_amount += total_price
        items.append(
            CartItemOut(
                product=product,
                quantity=int(item["quantity"]),
                total_price=total_price,
            )
        )

    return CartOut(
        user_id=user_id,
        cart_items=items,
        total_amount=total_amount,
    )


async def remove_item(user_id: int, product_id: int, redis: Redis):
    cart_key = f"cart_{user_id}"
    removed = await redis.hdel(cart_key, str(product_id))
    if removed:
        return Response(content="Product removed from cart", status_code=200)
    raise HTTPException(status_code=404, detail="Product not found in cart")


async def remove_cart(user_id: int, redis: Redis):
    cart_key = f"cart_{user_id}"
    deleted = await redis.delete(cart_key)
    if deleted:
        return Response(content="Cart successfully removed", status_code=200)
    raise HTTPException(status_code=404, detail="Cart not found")
