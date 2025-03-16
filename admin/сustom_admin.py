import requests
import io
from sqladmin import Admin
from fastapi import Request
from typing import Any
from starlette.datastructures import FormData, UploadFile
from utils.s3_utils import get_s3_url


class CustomAdmin(Admin):
    async def _handle_form_data(self, request: Request, obj: Any = None) -> FormData:
        """
        Заменённый метод в Admin
        Если есть текущий файл, но при изменении поле загрузки остаётся
        пустым - грузим старый файл и подставляем его в форму.
        """
        if obj:
            model_name = obj.__class__.__name__
            file_folder = model_name.lower() + "s"
        else:
            file_folder = "default_folder"

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
                    current_url = get_s3_url(
                        file_folder=file_folder, file_name=current_file
                    )
                    if isinstance(current_url, str) and current_url.startswith(
                        ("http://", "https://")
                    ):
                        try:
                            response = requests.get(current_url)
                            response.raise_for_status()
                            file_content = response.content
                            form_data.append(
                                (
                                    key,
                                    UploadFile(
                                        filename=current_url.split("/")[-1],
                                        file=io.BytesIO(file_content),
                                    ),
                                )
                            )
                        except Exception as e:
                            continue
            else:
                form_data.append((key, value))
        return FormData(form_data)
