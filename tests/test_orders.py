import pytest
from datetime import datetime
from tests.fixtures import (
    order_with_items,
    auth_headers_web,
    cart_with_items,
    products_with_sizes,
)
from decimal import Decimal
from services.redis_cart import CartDO


def normalize_order(order):
    return {
        "id": order["id"],
        "user_order_id": order["user_order_id"],
        "total_amount": Decimal(order["total_amount"]),
        "status": order["status"],
        "order_items": sorted(
            [
                {
                    "product_id": item["product_id"],
                    "size_id": item["size_id"],
                    "name": item["name"].lower(),
                    "size_name": item["size_name"].lower(),
                    "quantity": item["quantity"],
                    "total_price": Decimal(item["total_price"]),
                }
                for item in order["order_items"]
            ],
            key=lambda x: (x["product_id"], x["size_id"]),
        ),
        "delivery": {
            "delivery_type": order["delivery"]["delivery_type"],
            "delivery_address": order["delivery"]["delivery_address"].lower(),
        },
        "created_at": datetime.fromisoformat(order["created_at"]),
        "updated_at": datetime.fromisoformat(order["updated_at"]),
    }


@pytest.mark.asyncio
async def test_get_all_orders(
    client,
    order_with_items,
    test_cache_manager,
    auth_headers_web,
    test_session,
    mocker,
):
    headers, user = auth_headers_web
    response = await client.get("/orders/", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data) == len(order_with_items)
    assert all(order["id"] in [o.id for o in order_with_items] for order in data)
    fetch_from_db_mock = mocker.patch(
        "db.operations.OrderDO.get_all",
        return_value=[],
    )

    response2 = await client.get("/orders/", headers=headers)
    assert response2.status_code == 200
    normalize_data = [normalize_order(order) for order in data]
    normalize_response2 = [normalize_order(order) for order in response2.json()]
    assert normalize_data == normalize_response2

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_orders_by_status(
    client,
    order_with_items,
    auth_headers_web,
    mocker,
):
    headers, user = auth_headers_web

    statuses = {order.status for order in order_with_items}

    for status in statuses:
        response = await client.get(f"/orders/?status={status}", headers=headers)
        assert response.status_code == 200

        data = response.json()

        assert all(order["status"] == status for order in data)

        fetch_from_db_mock = mocker.patch(
            "db.operations.OrderDO.get_all",
            return_value=[],
        )

        response2 = await client.get(f"/orders/?status={status}", headers=headers)
        assert response2.status_code == 200
        normalize_data = [normalize_order(order) for order in data]
        normalize_response2 = [normalize_order(order) for order in response2.json()]
        assert normalize_data == normalize_response2

        fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_order_history(
    client,
    order_with_items,
    auth_headers_web,
    test_cache_manager,
    mocker,
):
    headers, user = auth_headers_web

    completed_orders = [
        order for order in order_with_items if order.status == "completed"
    ]

    response1 = await client.get("/orders/history/", headers=headers)
    assert response1.status_code == 200
    data = response1.json()

    assert len(data) == len(completed_orders)

    fetch_from_db_mock = mocker.patch(
        "db.operations.OrderDO.get_all_by_status",
        return_value=[],
    )

    response2 = await client.get("/orders/history/", headers=headers)
    assert response2.status_code == 200
    normalize_data = [normalize_order(order) for order in data]
    normalize_response2 = [normalize_order(order) for order in response2.json()]

    assert normalize_data == normalize_response2

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_orders(
    client,
    order_with_items,
    auth_headers_web,
    test_cache_manager,
    mocker,
):
    headers, user = auth_headers_web

    current_orders = [
        order for order in order_with_items if order.status != "completed"
    ]

    response1 = await client.get("/orders/current/", headers=headers)
    assert response1.status_code == 200
    data = response1.json()

    assert len(data) == len(current_orders)

    fetch_from_db_mock = mocker.patch(
        "db.operations.OrderDO.get_all_by_statuses",
        return_value=[],
    )

    response2 = await client.get("/orders/current/", headers=headers)
    assert response2.status_code == 200
    normalize_data = [normalize_order(order) for order in data]
    normalize_response2 = [normalize_order(order) for order in response2.json()]

    assert normalize_data == normalize_response2

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_order(
    client,
    order_with_items,
    auth_headers_web,
    test_cache_manager,
    mocker,
):
    headers, user = auth_headers_web
    order = order_with_items[0]
    order_id = order.id

    response1 = await client.get(f"/orders/{order_id}/", headers=headers)
    assert response1.status_code == 200
    data = response1.json()

    assert data["id"] == order.id
    assert data["user_order_id"] == order.user_order_id
    assert Decimal(data["total_amount"]) == Decimal(order.total_amount)
    assert data["status"] == order.status
    assert data["delivery"]["delivery_type"] == order.delivery.delivery_type
    assert data["delivery"]["delivery_address"] == order.delivery.delivery_address

    assert len(data["order_items"]) == len(order.order_items)
    for item1, item2 in zip(data["order_items"], order.order_items):
        assert item1["product_id"] == item2.product_id
        assert item1["size_id"] == item2.size_id
        assert item1["name"] == item2.name
        assert item1["size_name"] == item2.size_name
        assert item1["quantity"] == item2.quantity
        assert Decimal(item1["total_price"]) == Decimal(item2.total_price)

    fetch_from_db_mock = mocker.patch(
        "db.operations.OrderDO.get_by_id",
        return_value=[],
    )

    response2 = await client.get(f"/orders/{order_id}/", headers=headers)
    assert response2.status_code == 200
    assert normalize_order(response2.json()) == normalize_order(data)

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_confirmation_order(
    client,
    cart_with_items,
    auth_headers_web,
    test_redis,
):
    user_id, cart_key, items, headers, products, sizes = cart_with_items

    response = await client.post(
        "/orders/confirmation/",
        headers=headers,
        json={
            "delivery_type": "courier",
            "delivery_address": "Test Address",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Order successfully created",
    }

    cart_items = await test_redis.hgetall(cart_key)
    assert not cart_items


@pytest.mark.asyncio
async def test_repeat_order_to_cart(
    client,
    order_with_items,
    auth_headers_web,
    test_redis,
    test_session,
):
    headers, user = auth_headers_web
    order = order_with_items[0]
    order_id = order.id

    cart = await CartDO.get_cart(user_id=user.id, redis=test_redis, session=test_session)
    assert not cart or not cart.cart_items

    response = await client.post(f"/orders/repeat/{order_id}/", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Products from the order have been added to the cart"
    }

    cart_after = await CartDO.get_cart(user_id=user.id, redis=test_redis, session=test_session)
    assert cart_after is not None
    assert cart_after.cart_items
    assert len(cart_after.cart_items) == len(order.order_items)
