import pytest
import json
from decimal import Decimal, ROUND_HALF_UP
from db.operations import ProductDO
from tests.fixtures import (
    cart_with_items, # noqa: F401
    auth_headers_web, # noqa: F401
    products_with_sizes, # noqa: F401
    empty_cart, # noqa: F401
)


@pytest.mark.asyncio
async def test_add_item_to_cart_new_item(
    client,
    test_redis,
    empty_cart,
):
    _, cart_key, _, headers, products, sizes = empty_cart
    product = products[0]
    size = sizes[0]

    response = await client.post(
        f"/carts/add/{product.id}/{size.id}/",
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json() == {"message": "Product added to cart"}

    cart_item_id = f"{product.id}:{size.id}"
    item_data = await test_redis.hget(cart_key, cart_item_id)
    assert item_data is not None

    item = json.loads(item_data)
    assert item["product_id"] == product.id
    assert item["size_id"] == size.id
    assert item["quantity"] == 1


@pytest.mark.asyncio
async def test_add_item_to_cart_existing_item(
    client,
    test_redis,
    empty_cart,
):
    _, cart_key, _, headers, products, sizes = empty_cart
    product = products[0]
    size = sizes[0]

    await client.post(
        f"/carts/add/{product.id}/{size.id}/",
        headers=headers,
    )

    response = await client.post(
        f"/carts/add/{product.id}/{size.id}/",
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json() == {"message": "Product added to cart"}

    cart_item_id = f"{product.id}:{size.id}"
    item_data = await test_redis.hget(cart_key, cart_item_id)
    assert item_data is not None

    item = json.loads(item_data)
    assert item["quantity"] == 2


@pytest.mark.asyncio
async def test_update_cart_item_quantity(
    client,
    test_redis,
    cart_with_items,
):
    _, cart_key, _, headers, products, sizes = cart_with_items
    product = products[0]
    size = sizes[0]

    update_data = {"quantity": 5}
    response = await client.patch(
        f"/carts/update/{product.id}/{size.id}/",
        json=update_data,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Product quantity updated"}

    cart_item_id = f"{product.id}:{size.id}"
    item_data = await test_redis.hget(cart_key, cart_item_id)
    assert item_data is not None

    item = json.loads(item_data)
    assert item["quantity"] == 5


@pytest.mark.asyncio
async def test_get_cart_user(
    client,
    test_session,
    test_redis,
    cart_with_items,
):
    _, _, items, headers, products, sizes = cart_with_items

    response = await client.get("/carts/", headers=headers)
    assert response.status_code == 200

    cart_data = response.json()
    assert len(cart_data["cart_items"]) == len(items)

    total_amount = Decimal("0.00")

    for item in cart_data["cart_items"]:
        assert item["product"]["id"] in [product.id for product in products]
        assert item["product"]["size_id"] in [size.id for size in sizes]
        # assert item["quantity"] == 5
        for p_id, s_id, qty in items:
            if (
                p_id == item["product"]["id"]
                and s_id == item["product"]["size_id"]
            ):
                assert item["quantity"] == qty
                break

        product_size = await ProductDO.get_for_id_by_size_id(
            product_id=item["product"]["id"],
            size_id=item["product"]["size_id"],
            session=test_session,
        )
        expected_price = (
            product_size.price * (1 - Decimal(product_size.discount) / 100)
        )
        expected_price = expected_price.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        assert (
                Decimal(item["total_price"])
                == expected_price * item["quantity"]
        )

        total_amount += Decimal(item["total_price"])

    assert Decimal(cart_data["total_amount"]) == total_amount


@pytest.mark.asyncio
async def test_get_cart_item_user(
    client,
    test_session,
    test_redis,
    cart_with_items,
):
    _, _, items, headers, products, sizes = cart_with_items
    product = products[0]
    size = sizes[0]

    response = await client.get(
        f"/carts/{product.id}/{size.id}/",
        headers=headers,
    )
    assert response.status_code == 200

    for p_id, s_id, qty in items:
        if p_id == product.id and s_id == size.id:
            expected_quantity = qty
            break
    item_data = response.json()
    assert item_data["product"]["id"] == product.id
    assert item_data["product"]["size_id"] == size.id
    assert item_data["quantity"] == expected_quantity

    product_size = await ProductDO.get_for_id_by_size_id(
        product_id=product.id,
        size_id=size.id,
        session=test_session,
    )
    assert product_size is not None

    discount_decimal = Decimal(product_size.discount) / Decimal(100)
    expected_price = product_size.price * (1 - discount_decimal)
    expected_price = (
        expected_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )

    assert (
    Decimal(item_data["total_price"])
    == expected_price * item_data["quantity"]
    )


@pytest.mark.asyncio
async def test_delete_item_from_cart(
    client,
    test_redis,
    cart_with_items,
):
    _, cart_key, _, headers, products, sizes = cart_with_items
    product = products[0]
    size = sizes[0]

    response = await client.delete(
        f"/carts/delete/{product.id}/{size.id}/",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Product removed from cart"}

    cart_item_id = f"{product.id}:{size.id}"
    item_data = await test_redis.hget(cart_key, cart_item_id)
    assert item_data is None


@pytest.mark.asyncio
async def test_delete_item_not_in_cart(
    client,
    test_redis,
    cart_with_items,
):
    _, cart_key, _, headers, products, sizes = cart_with_items
    product = products[0]
    size = sizes[0]

    await test_redis.hdel(cart_key, f"{product.id}:{size.id}")

    response = await client.delete(
        f"/carts/delete/{product.id}/{size.id}/",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found in cart"}


@pytest.mark.asyncio
async def test_delete_cart(
    client,
    test_redis,
    cart_with_items,
):
    _, cart_key, _, headers, _, _ = cart_with_items

    response = await client.delete(
        "/carts/",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Cart successfully removed"}

    cart_items = await test_redis.hgetall(cart_key)
    assert not cart_items


@pytest.mark.asyncio
async def test_delete_cart_empty(
    client,
    test_redis,
    cart_with_items,
):
    _, cart_key, _, headers, _, _ = cart_with_items

    await test_redis.delete(cart_key)

    response = await client.delete(
        "/carts/",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Cart not found"}
