import pytest
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from tests.fixtures import products_with_sizes


def normalize_product(product):
    """
    Нормализует продукт для сравнения
    """
    return {
        "id": product["id"],
        "name": product["name"],
        "description": product["description"],
        "photo_name": product["photo_name"],
        "category_id": product["category_id"],
        "created_at": datetime.fromisoformat(product["created_at"]),
        "updated_at": datetime.fromisoformat(product["updated_at"]),
        "product_sizes": [
            {
                "price": Decimal(product_size["price"]),
                "discount": product_size["discount"],
                "final_price": Decimal(product_size["final_price"]),
                "created_at": (
                    datetime.fromisoformat(product_size["created_at"])
                ),
                "updated_at": (
                    datetime.fromisoformat(product_size["updated_at"])
                ),
                "size": {
                    "id": product_size["size"]["id"],
                    "name": product_size["size"]["name"],
                },
            }
            for product_size in product["product_sizes"]
        ],
    }


@pytest.mark.asyncio
async def test_get_all_products(
    client,
    products_with_sizes,
    test_cache_manager,
    mocker,
):
    """
    Тест проверки получения списка продуктов и
    проверки подсчёта final_price
    """
    products, sizes, product_sizes = products_with_sizes
    response = await client.get("/products/")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == len(products)
    for i, product in enumerate(products):
        assert data[i]["id"] == product.id
        assert data[i]["name"] == product.name
        assert data[i]["description"] == product.description
        assert data[i]["photo_name"] == product.photo_name

        assert len(data[i]["product_sizes"]) == len(sizes)
        for j, product_size_data in enumerate(data[i]["product_sizes"]):
            assert product_size_data["size"]["id"] == sizes[j].id
            assert product_size_data["size"]["name"] == sizes[j].name
            assert (
                Decimal(product_size_data["price"])
                == product_sizes[i * len(sizes) + j].price
            )
            assert (
                Decimal(product_size_data["discount"])
                == product_sizes[i * len(sizes) + j].discount
            )

            price = Decimal(product_size_data["price"])
            discount = Decimal(product_size_data["discount"])
            discount_decimal = discount / Decimal(100)
            expected_final_price = (
                (price - (price * discount_decimal))
                .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )

            assert (
                Decimal(product_size_data["final_price"])
                == expected_final_price
            )
    fetch_from_db_mock = mocker.patch(
        "db.operations.ProductDO.get_all", return_value=[]
    )

    response2 = await client.get("/products/")
    assert response2.status_code == 200

    normalized_data = [normalize_product(product) for product in data]
    normalized_response2 = [
        normalize_product(product) for product in response2.json()
    ]

    assert normalized_response2 == normalized_data

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_products_by_category(
    client,
    products_with_sizes,
    test_cache_manager,
    mocker,
):
    """
    Тест получения продуктов по категории
    """
    products, _, _ = products_with_sizes

    category_id = products[0].category_id

    response = await client.get(f"/products/?category_id={category_id}")
    assert response.status_code == 200

    data = response.json()

    for product_data in data:
        assert product_data["category_id"] == category_id

    fetch_from_db_mock = mocker.patch(
        "db.operations.ProductDO.get_all_by_category_id",
        return_value=[],
    )

    response2 = await client.get(f"/products/?category_id={category_id}")
    assert response2.status_code == 200
    normalized_data = [normalize_product(product) for product in data]
    normalized_response2 = [
        normalize_product(product) for product in response2.json()
    ]
    assert normalized_response2 == normalized_data

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_product_by_id(
    client,
    products_with_sizes,
    test_cache_manager,
    mocker,
):
    """
    Тест получения продукта по id
    """
    products, _, _ = products_with_sizes

    product = products[0]

    response = await client.get(f"/products/{product.id}/")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product.id
    assert data["name"] == product.name
    assert data["description"] == product.description
    assert data["photo_name"] == product.photo_name
    assert data["category_id"] == product.category_id
    fetch_from_db_mock = mocker.patch(
        "db.operations.ProductDO.get_by_id",
        return_value=None,
    )

    response2 = await client.get(f"/products/{product.id}/")
    assert response2.status_code == 200
    normalized_data = normalize_product(data)
    normalized_response2 = normalize_product(response2.json())
    assert normalized_response2 == normalized_data

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_product_by_id_not_found(client):
    """
    Тест получения несуществующего продукта
    """
    non_existent_product_id = 999

    response = await client.get(f"/products/{non_existent_product_id}/")
    assert response.status_code == 404

    assert response.json()["detail"] == "Product not found"
