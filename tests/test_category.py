import pytest
from db.operations import CategoryDO
from fastapi_cache import FastAPICache


@pytest.mark.asyncio
async def test_get_categories(client, test_session, test_cache_manager, mocker):
    await CategoryDO.add(test_session, name="Category 1")
    await CategoryDO.add(test_session, name="Category 2")

    response = await client.get("/category/")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Category 1"
    assert data[1]["name"] == "Category 2"

    fetch_from_db_mock = mocker.patch(
        "db.operations.CategoryDO.get_all",
        return_value=[],
    )

    response2 = await client.get("/category/")
    assert response2.status_code == 200
    assert response2.json() == data

    fetch_from_db_mock.assert_not_called()