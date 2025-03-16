import pytest
from db.operations import ProductDO


@pytest.mark.asyncio
async def test_get_all_products(
    client,
    test_session,
    test_cache_manager,
    mocker,
):
    await ProductDO.add(test_session, name="Product 1", category_id=1)
    await ProductDO.add(test_session, name="Product 2", category_id=2)
    await ProductDO.add(test_session, name="Product 3", category_id=1)

    response = await client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Product 1"
    assert data[1]["name"] == "Product 2"

    fetch_from_db_mock = mocker.patch(
        "db.operations.ProductDO.get_all", return_value=[]
    )

    response2 = await client.get("/products/")
    assert response2.status_code == 200
    assert response2.json() == data

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_products_by_category(
    client,
    test_session,
    test_cache_manager,
    mocker,
):
    response1 = await client.get("/products/?category_id=1")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 2
    assert data1[0]["name"] == "Product 1"
    assert data1[1]["name"] == "Product 3"

    fetch_from_db_mock = mocker.patch(
        "db.operations.ProductDO.get_all_by_category_id",
        return_value=[],
    )

    response2 = await client.get("/products/?category_id=1")
    assert response2.status_code == 200
    assert response2.json() == data1

    fetch_from_db_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_product_by_id(
    client,
    test_session,
    test_cache_manager,
    mocker,
):
    product = await ProductDO.add(test_session, name="Product One", category_id=1)
    response1 = await client.get(f"/products/{product.id}/")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["name"] == "Product One"

    fetch_from_db_mock = mocker.patch(
        "db.operations.ProductDO.get_by_id",
        return_value=None,
    )

    response2 = await client.get(f"/products/{product.id}/")
    assert response2.status_code == 200
    assert response2.json() == data1

    fetch_from_db_mock.assert_not_called()
