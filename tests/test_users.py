import pytest
from config import settings
from db.operations import UserDO
from services.auth import (
    create_email_confirmation_token,
    create_refresh_token,
)
from fixtures import (
    web_user,
    tg_user,
    auth_headers_web,
    auth_headers_tg,
)


@pytest.mark.asyncio
async def test_register_web_user(
    client,
    test_session,
    test_redis,
    mocker,
):
    mock_bg_task = mocker.patch("fastapi.BackgroundTasks.add_task")
    user_data = {"email": "test@example.com", "password": "testpassword"}
    response = await client.post("/users/register/", json=user_data)

    assert response.status_code == 200
    assert (
        "Check your email to confirm registration."
        in response.json()["message"]
    )

    keys = await test_redis.keys("confirm:*")
    assert len(keys) > 0
    mock_bg_task.assert_called_once()


@pytest.mark.asyncio
async def test_register_tg_user(
    client,
    test_session,
    test_redis,
    mocker,
):
    mock_bg_task = mocker.patch("fastapi.BackgroundTasks.add_task")
    user_data = {"email": "test@example.com", "tg_id": "tg12345"}
    response = await client.post("/users/register/", json=user_data)

    assert response.status_code == 200
    assert (
        "Check your email to confirm registration."
        in response.json()["message"]
    )

    keys = await test_redis.keys("confirm:*")
    assert len(keys) > 0
    mock_bg_task.assert_called_once()


@pytest.mark.asyncio
async def test_register_tg_after_web(
    client,
    test_session,
    test_redis,
    web_user,
    mocker,
):
    mock_bg_task = mocker.patch("fastapi.BackgroundTasks.add_task")
    user_data = {"email": web_user.email, "tg_id": "tg12345"}
    response = await client.post("/users/register/", json=user_data)

    assert response.status_code == 200
    keys = await test_redis.keys("confirm:*")
    assert len(keys) > 0

    token = keys[0].split(":")[1]
    await client.get(f"/users/confirm-email/{token}/")

    user = await UserDO.get_by_email(
        email=web_user.email,
        session=test_session,
    )
    assert user is not None
    assert user.hashed_password == web_user.hashed_password
    assert user.tg_id == "tg12345"
    mock_bg_task.assert_called_once()


@pytest.mark.asyncio
async def test_register_web_after_tg(
    client,
    test_session,
    test_redis,
    tg_user,
    mocker,
):
    mock_bg_task = mocker.patch("fastapi.BackgroundTasks.add_task")
    user_data = {"email": tg_user.email, "password": "testpassword"}
    response = await client.post("/users/register/", json=user_data)

    assert response.status_code == 200
    keys = await test_redis.keys("confirm:*")
    assert len(keys) > 0

    token = keys[0].split(":")[1]
    await client.get(f"/users/confirm-email/{token}/")

    user = await UserDO.get_by_email(
        email=tg_user.email,
        session=test_session,
    )
    assert user is not None
    assert user.tg_id == tg_user.tg_id
    assert user.hashed_password is not None
    mock_bg_task.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_email_web(
    client,
    test_session,
    test_redis,
    web_user,
):
    token = create_email_confirmation_token(web_user.email)

    await test_redis.hset(
        f"confirm:{token}",
        mapping={
            "email": web_user.email,
            "hashed_password": web_user.hashed_password,
        },
    )

    response = await client.get(f"/users/confirm-email/{token}/")

    assert response.status_code == 200
    assert "Email successfully confirmed!" in response.json()["message"]

    user = await UserDO.get_by_email(
        email=web_user.email,
        session=test_session,
    )
    assert user is not None
    assert user.hashed_password == web_user.hashed_password


@pytest.mark.asyncio
async def test_confirm_email_tg(
    client,
    test_session,
    test_redis,
    tg_user,
):
    token = create_email_confirmation_token(tg_user.email)

    await test_redis.hset(
        f"confirm:{token}",
        mapping={
            "email": tg_user.email,
            "tg_id": tg_user.tg_id,
        }
    )

    response = await client.get(f"/users/confirm-email/{token}/")

    assert response.status_code == 200
    assert "Email successfully confirmed!" in response.json()["message"]

    user = await UserDO.get_by_email(
        email=tg_user.email,
        session=test_session,
    )
    assert user is not None
    assert user.tg_id == tg_user.tg_id


@pytest.mark.asyncio
async def test_login_user(client, web_user):
    response = await client.post(
        "/users/login/", json={
            "email": web_user.email,
            "password": "testpassword",
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


@pytest.mark.asyncio
async def test_login_user_invalid_password(client, web_user):
    response = await client.post(
        "/users/login/", json={
            "email": web_user.email,
            "password": "wrongpassword",
        }
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout_user(client, auth_headers_web):
    headers, _ = auth_headers_web
    response = await client.post("/users/logout/", headers=headers)

    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_profile_web(client, auth_headers_web):
    headers, user = auth_headers_web
    response = await client.get(
        "/users/profile/",
        headers=headers,
    )
    profile_data = response.json()

    assert response.status_code == 200
    assert profile_data["email"] == user.email


@pytest.mark.asyncio
async def test_get_profile_tg(client, auth_headers_tg):
    headers, user = auth_headers_tg
    response = await client.get(
        "/users/profile/",
        headers=headers,
    )
    profile_data = response.json()

    assert response.status_code == 200
    assert profile_data["email"] == user.email
    assert profile_data["tg_id"] == user.tg_id


@pytest.mark.asyncio
async def test_refresh_access_token(client, web_user):
    refresh_token = create_refresh_token(
        data={"email": web_user.email}, secret_key=settings.SECRET_KEY
    )
    response = await client.post(
        "/users/token/refresh/", json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_access_token_invalid(client):
    response = await client.post(
        "/users/token/refresh/", json={"refresh_token": "invalidtoken"}
    )

    assert response.status_code == 401
