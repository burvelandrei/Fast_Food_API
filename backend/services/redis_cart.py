import json
from redis.asyncio import Redis
from schemas.cart import CartItemCreate

async def add_to_cart(user_id: int, cart_item: CartItemCreate, redis: Redis):
    cart_key = f"cart_{user_id}"
    existing_item = await redis.hget(cart_key, str(cart_item.product_id))

    if existing_item:
        existing_item = json.loads(existing_item)
        existing_item["quantity"] = cart_item.quantity
    else:
        existing_item = cart_item.dict()
    cart_items = await redis.hgetall(cart_key)
    if cart_items:
        await redis.hset(cart_key, str(cart_item.product_id), json.dumps(existing_item))
    else:
        await redis.hset(cart_key, str(cart_item.product_id), json.dumps(existing_item))
        await redis.expire(cart_key, 24*60*60)
    return {"message": f"Product add to cart"}


async def get_cart(user_id: int, redis: Redis):
    cart_key = f"cart_{user_id}"
    cart_items = await redis.hgetall(cart_key)
    if cart_items:
        return [json.loads(item) for item in cart_items.values()]
    return []


async def get_cart_item(user_id: int, product_id: int, redis: Redis):
    cart_key = f"cart_{user_id}"
    cart_item = await redis.hget(cart_key, str(product_id))
    if cart_item:
        return json.loads(cart_item)
    return {}


async def remove_item(user_id: int, product_id: int, redis: Redis):
    cart_key = f"cart_{user_id}"
    await redis.hdel(cart_key, str(product_id))


async def remove_cart(user_id: int, redis: Redis):
    cart_key = f"cart_{user_id}"
    await redis.delete(cart_key)
