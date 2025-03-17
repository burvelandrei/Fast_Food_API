import logging
import logging.config
import json
from redis.asyncio import Redis
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.operations import ProductDO
from schemas.cart import (
    CartItemModify,
    CartItemOut,
    CartOut,
    CartItemCreate,
    ProductCartOut,
)
from utils.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("redis_operations")


class CartDO:
    """
    Класс с операциями для cart и cartitem
    """

    @staticmethod
    async def add_to_cart(
        product_id: int,
        size_id: int,
        user_id: int,
        redis: Redis,
        session: AsyncSession,
    ):
        """Добавление продукта в корзину"""
        logger.info(
            f"Adding product {product_id} size {size_id} to user_id "
            f"{user_id} cart"
        )
        product_size = await ProductDO.get_for_id_by_size_id(
            product_id=product_id,
            size_id=size_id,
            session=session,
        )
        if not product_size:
            logger.warning(f"Product {product_id} size {size_id} not found")
            raise HTTPException(
                status_code=404,
                detail="Product not found in database",
            )

        cart_key = f"cart:{user_id}"
        cart_item_id = f"{product_id}:{size_id}"
        existing_item = await redis.hget(cart_key, cart_item_id)

        if existing_item:
            existing_item = json.loads(existing_item)
            existing_item["quantity"] += 1
        else:
            existing_item = CartItemCreate(
                product_id=product_id,
                size_id=size_id,
                quantity=1,
            ).__dict__
        cart_items = await redis.hlen(cart_key)
        await redis.hset(cart_key, cart_item_id, json.dumps(existing_item))
        if not cart_items:
            await redis.expire(cart_key, 60 * 60)

    @staticmethod
    async def update_cart_item(
        product_id: int,
        size_id: int,
        quantity: CartItemModify,
        user_id: int,
        redis: Redis,
        session: AsyncSession,
    ):
        """Обновление количества продукта в корзине"""
        logger.info(
            f"Updating product {product_id} size {size_id} in user_id "
            f"{user_id} cart"
        )
        cart_key = f"cart:{user_id}"
        cart_item_id = f"{product_id}:{size_id}"
        existing_item = await redis.hget(cart_key, cart_item_id)
        product_size = await ProductDO.get_for_id_by_size_id(
            product_id=product_id,
            size_id=size_id,
            session=session,
        )
        if not product_size:
            logger.warning(f"Product {product_id} size {size_id} not found")
            raise HTTPException(
                status_code=404,
                detail="Product not found in database",
            )

        if not existing_item:
            logger.warning(
                f"Product {product_id} size {size_id} not found in cart"
            )
            raise HTTPException(
                status_code=404,
                detail="Product not found in cart",
            )

        existing_item = json.loads(existing_item)
        existing_item["quantity"] = quantity
        await redis.hset(cart_key, cart_item_id, json.dumps(existing_item))

    @staticmethod
    async def get_cart(
        user_id: int,
        redis: Redis,
        session: AsyncSession,
    ):
        """Получение корзины по user_id"""
        logger.info(f"Fetching cart for user {user_id}")
        cart_key = f"cart:{user_id}"
        cart_items = await redis.hgetall(cart_key)

        if not cart_items:
            return CartOut(
                cart_items=[],
                total_amount=0,
            )
        items = []
        for cart_item_id, item_data in cart_items.items():
            item = json.loads(item_data)
            product_id = item["product_id"]
            size_id = item["size_id"]
            item = json.loads(item_data)
            product_size = await ProductDO.get_for_id_by_size_id(
                product_id=product_id,
                size_id=size_id,
                session=session,
            )
            if not product_size:
                logger.warning(
                    f"Product {product_id} size {size_id} not found in DB, "
                    f"removing from cart"
                )
                await redis.hdel(cart_key, cart_item_id)
                continue
            product_data = ProductCartOut(
                id=product_size.product.id,
                name=product_size.product.name,
                description=product_size.product.description,
                photo_name=product_size.product.photo_name,
                size_id=product_size.size.id,
                size_name=product_size.size.name,
                price=product_size.price,
                discount=product_size.discount,
            )
            items.append(
                CartItemOut(
                    product=product_data,
                    quantity=item["quantity"],
                )
            )
        return CartOut(
            cart_items=items,
        )

    @staticmethod
    async def get_cart_item(
        product_id: int,
        size_id: int,
        user_id: int,
        redis: Redis,
        session: AsyncSession,
    ):
        """Получение одного товара из корзины"""
        logger.info(
            f"Fetching product {product_id} size {size_id} from user "
            f"{user_id} cart"
        )
        cart_key = f"cart:{user_id}"
        cart_item_id = f"{product_id}:{size_id}"
        item_data = await redis.hget(cart_key, cart_item_id)

        if not item_data:
            logger.warning(
                f"Product {product_id} size {size_id} not found in cart"
            )
            raise HTTPException(
                status_code=404,
                detail="Product not found in cart",
            )

        item = json.loads(item_data)
        product_size = await ProductDO.get_for_id_by_size_id(
            product_id=product_id,
            size_id=size_id,
            session=session,
        )
        if not product_size:
            logger.warning(f"Product {product_id} not found in database")
            raise HTTPException(status_code=404, detail="Product not found")
        product_data = ProductCartOut(
            id=product_size.product.id,
            name=product_size.product.name,
            description=product_size.product.description,
            photo_name=product_size.product.photo_name,
            size_id=product_size.size.id,
            size_name=product_size.size.name,
            price=product_size.price,
            discount=product_size.discount,
        )
        return CartItemOut(
            product=product_data,
            quantity=item["quantity"],
        )

    @staticmethod
    async def remove_item(
        product_id: int,
        size_id: int,
        user_id: int,
        redis: Redis,
    ):
        """Удаление продукта из корзины"""
        logger.info(
            f"Removing product {product_id} size {size_id} from user_id "
            f"{user_id} cart"
        )
        cart_key = f"cart:{user_id}"
        cart_item_id = f"{product_id}:{size_id}"
        removed = await redis.hdel(cart_key, cart_item_id)
        if not removed:
            logger.warning(
                f"Product {product_id} size {size_id} not found in cart "
                f"{cart_key}"
            )
            raise HTTPException(
                status_code=404,
                detail="Product not found in cart",
            )

    @staticmethod
    async def remove_cart(user_id: int, redis: Redis):
        """Очистка корзины"""
        logger.info(f"Clearing cart for user {user_id}")
        cart_key = f"cart:{user_id}"
        deleted = await redis.delete(cart_key)
        if not deleted:
            logger.warning(f"Cart {cart_key} not found")
            raise HTTPException(status_code=404, detail="Cart not found")

    @staticmethod
    async def repeat_item_to_cart(
        cart_item: CartItemCreate,
        user_id: int,
        redis: Redis,
        session: AsyncSession,
    ):
        """Повторяет продукты в корзину из заказа по id"""
        logger.info(
            f"Adding product {cart_item.product_id} size "
            f"{cart_item.size_id} to user_id {user_id} cart"
        )
        product_size = await ProductDO.get_for_id_by_size_id(
            product_id=cart_item.product_id,
            size_id=cart_item.size_id,
            session=session,
        )
        if not product_size:
            logger.warning(
                f"Skipping product {cart_item.product_id} size "
                f"{cart_item.size_id} - not found in database"
            )
            return

        cart_key = f"cart:{user_id}"
        cart_item_id = f"{cart_item.product_id}:{cart_item.size_id}"
        cart_items = await redis.hlen(cart_key)
        await redis.hset(
            cart_key,
            cart_item_id,
            json.dumps(cart_item.__dict__),
        )
        if not cart_items:
            await redis.expire(cart_key, 60 * 60)
