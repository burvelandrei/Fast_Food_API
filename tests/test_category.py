import pytest
from tests.fixtures import category


@pytest.mark.asyncio
async def test_get_categorу(
    client,
    category,
    test_cache_manager,
    mocker,
):
    response = await client.get("/category/")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == len(category)
    for i, category in enumerate(category):
        assert data[i]["name"] == category.name

    fetch_from_db_mock = mocker.patch(
        "db.operations.CategoryDO.get_all",
        return_value=[],
    )

    response2 = await client.get("/category/")
    assert response2.status_code == 200
    assert response2.json() == data

    fetch_from_db_mock.assert_not_called()
