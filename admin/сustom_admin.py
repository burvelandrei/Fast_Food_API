import io
from sqladmin import Admin
from fastapi import Request
from typing import Any
from starlette.datastructures import FormData, UploadFile


class CustomAdmin(Admin):
    async def _handle_form_data(
        self,
        request: Request,
        obj: Any = None,
    ) -> FormData:
        """
        Заменённый метод в Admin
        Если есть текущий файл, но при изменении поле загрузки остаётся
        пустым - возвращаем в форму старый файл в виде str.
        """
        form = await request.form()
        form_data: list[tuple[str, str | UploadFile]] = []
        for key, value in form.multi_items():
            if not isinstance(value, UploadFile):
                form_data.append((key, value))
                continue

            should_clear = form.get(key + "_checkbox")
            empty_upload = len(await value.read(1)) != 1
            await value.seek(0)

            if should_clear:
                form_data.append((key, UploadFile(io.BytesIO(b""))))
            elif empty_upload and obj:
                current_file = getattr(obj, key, None)
                if current_file:
                    form_data.append((key, current_file))
            else:
                form_data.append((key, value))
        return FormData(form_data)
