import typing
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CookieMiddleware:
    """
    Класс middleware который позволяет устанавливать
    cookies в ответе и читать cookies из запроса.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Читает cookies из запроса и добавляет функцию для
        установки cookies в ответ.
        """
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        scope["cookies"] = connection.cookies
        scope["set_cookie"] = self.set_cookie(scope)

        # Обёртка для функции send для добавления заголовка Set-Cookie в ответ
        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                if "_cookies_to_set" in scope:
                    for (
                        cookie_name,
                        cookie_value,
                    ) in scope["_cookies_to_set"].items():
                        headers.append("Set-Cookie", cookie_value)
                    del scope["_cookies_to_set"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def set_cookie(self, scope: Scope):
        """
        Функция для установки cookies в ответе.
        """

        def _set_cookie(
            name: str,
            value: str,
            max_age: int | None = None,
            path: str | None = None,
            domain: str | None = None,
            secure: bool = False,
            httponly: bool = True,
            samesite: typing.Literal["lax", "strict", "none"] = "lax",
        ):
            cookie_parts = [f"{name}={value}"]
            if max_age is not None:
                cookie_parts.append(f"Max-Age={max_age}")
            if path:
                cookie_parts.append(f"Path={path}")
            if domain:
                cookie_parts.append(f"Domain={domain}")
            if secure and scope.get("scheme") == "https":
                cookie_parts.append("Secure")
            if httponly:
                cookie_parts.append("HttpOnly")
            cookie_parts.append(f"SameSite={samesite}")

            if "_cookies_to_set" not in scope:
                scope["_cookies_to_set"] = {}

            scope["_cookies_to_set"][name] = "; ".join(cookie_parts)

        return _set_cookie
