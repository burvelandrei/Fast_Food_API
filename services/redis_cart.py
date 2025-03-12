import logging
import logging.config
import json
from redis.asyncio import Redis
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from db.operations import ProductDO
from schemas.cart import CartItemModify, CartItemOut, CartOut, CartItemСreate
from schemas.product import ProductOut
from utils.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("redis_operations")


async def add_to_cart(
    user_id: int,
    cart_item: CartItemСreate,
    redis: Redis,
    session: AsyncSession,
):
    """Добавление продукта в корзину или увеличение количества"""
    logger.info(f"Adding product {cart_item.product_id} to user_id {user_id} cart")
    product = await ProductDO.get_by_id(session=session, id=cart_item.product_id)
    if not product:
        logger.warning(f"Product {cart_item.product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found in database")

    cart_key = f"cart:{user_id}"
    existing_item = await redis.hget(cart_key, str(cart_item.product_id))

    if existing_item:
        existing_item = json.loads(existing_item)
        existing_item["quantity"] += cart_item.quantity
    else:
        existing_item = cart_item.dict()
    cart_items = await redis.hlen(cart_key)
    await redis.hset(cart_key, str(cart_item.product_id), json.dumps(existing_item))
    if not cart_items:
        await redis.expire(cart_key, 24 * 60 * 60)
    return JSONResponse(
        content={"message": "Product added to cart"},
        status_code=201,
    )


async def update_cart_item(
    product_id: int,
    user_id: int,
    quantity: CartItemModify,
    redis: Redis,
    session: AsyncSession,
):
    """Обновление количества продукта в корзине"""
    logger.info(f"Updating product {product_id} in user_id {user_id} cart")
    cart_key = f"cart:{user_id}"
    existing_item = await redis.hget(cart_key, str(product_id))
    product = await ProductDO.get_by_id(session=session, id=product_id)
    if not product:
        logger.warning(f"Product {product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found in database")

    if not existing_item:
        logger.warning(f"Product {product_id} not found in cart")
        raise HTTPException(status_code=404, detail="Product not found in cart")

    existing_item = json.loads(existing_item)
    existing_item["quantity"] = quantity
    await redis.hset(cart_key, str(product_id), json.dumps(existing_item))

    return JSONResponse(
        content={"message": "Product quantity updated"},
        status_code=200,
    )


async def get_cart(
    user_id: int,
    redis: Redis,
    session: AsyncSession,
):
    """Функция для получения корзины по user_id"""
    logger.info(f"Fetching cart for user {user_id}")
    cart_key = f"cart:{user_id}"
    cart_items = await redis.hgetall(cart_key)

    if not cart_items:
        return CartOut(
            cart_items=[],
            total_amount=0,
        )
    items = []
    total_amount = 0
    for product_id, item_data in cart_items.items():
        item = json.loads(item_data)
        product = await ProductDO.get_by_id(session=session, id=int(product_id))
        if not product:
            logger.warning(f"Product {product_id} not found in DB, removing from cart")
            await redis.hdel(cart_key, str(product_id))
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
        cart_items=items,
        total_amount=total_amount,
    )


async def get_cart_item(
    product_id: int,
    user_id: int,
    redis: Redis,
    session: AsyncSession,
):
    """Получение одного товара из корзины"""
    logger.info(f"Fetching product {product_id} from user {user_id} cart")
    cart_key = f"cart:{user_id}"
    item_data = await redis.hget(cart_key, str(product_id))

    if not item_data:
        logger.warning(f"Product {product_id} not found in cart")
        raise HTTPException(status_code=404, detail="Product not found in cart")

    item = json.loads(item_data)
    product = await ProductDO.get_by_id(session=session, id=product_id)
    if not product:
        logger.warning(f"Product {product_id} not found in database")
        raise HTTPException(status_code=404, detail="Product not found")

    product_out = ProductOut(**product.__dict__)
    total_price = product_out.final_price * item["quantity"]

    return CartItemOut(
        product=product_out,
        quantity=item["quantity"],
        total_price=total_price,
    )


async def remove_item(user_id: int, product_id: int, redis: Redis):
    """Удаление продукта из корзины"""
    logger.info(f"Removing product {product_id} from user_id {user_id} cart")
    cart_key = f"cart:{user_id}"
    removed = await redis.hdel(cart_key, str(product_id))
    if removed:
        return JSONResponse(
            content={"message": "Product removed from cart"},
            status_code=200,
        )
    logger.warning(f"Product {product_id} not found in cart {cart_key}")
    raise HTTPException(status_code=404, detail="Product not found in cart")


async def remove_cart(user_id: int, redis: Redis):
    """Очистка корзины"""
    logger.info(f"Clearing cart for user {user_id}")
    cart_key = f"cart:{user_id}"
    deleted = await redis.delete(cart_key)
    if deleted:
        return JSONResponse(
            content={"message": "Cart successfully removed"},
            status_code=200,
        )
    logger.warning(f"Cart {cart_key} not found")
    raise HTTPException(status_code=404, detail="Cart not found")
