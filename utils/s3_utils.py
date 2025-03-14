import boto3
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError
from botocore.config import Config
from config import settings


# Создаем клиент S3 с указанием ссылки на хранилище
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_HOST,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    use_ssl=False,
)


def check_file_exists(
    file_path: str,
):
    """
    Проверяет файл в хранилище S3
    """
    try:
        s3_client.head_object(
            Bucket=settings.S3_BACKET,
            Key=file_path,
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise e


async def upload_to_s3(file_folder: str, file: UploadFile) -> str:
    """
    Загружает файл в S3, если файл существует — выбрасывает ошибку
    """
    file_key = f"{settings.STATIC_DIR}/{file_folder}/{file.filename}"
    if check_file_exists(file_key):
        raise HTTPException(
            status_code=400,
            detail="Файл уже c таким именем уже существует",
        )

    s3_client.upload_fileobj(
        file.file,
        settings.S3_BACKET,
        file_key,
        ExtraArgs={"ACL": "public-read"},
    )

    return file.filename


def delete_from_s3(file_folder: str, file_name: str):
    """
    Удаляет файл из S3
    """
    if not file_folder or not file_name:
        return None
    file_path = f"{settings.STATIC_DIR}/{file_folder}/{file_name}"
    try:
        s3_client.delete_object(
            Bucket=settings.S3_BACKET,
            Key=file_path,
        )
    except Exception as e:
        raise e


def get_s3_url(file_folder: str, file_name: str):
    if not file_folder or not file_name:
        return None
    file_path = f"{settings.STATIC_DIR}/{file_folder}/{file_name}"
    if check_file_exists(file_path=file_path):
        return f"{settings.S3_HOST}/{settings.S3_BACKET}/{file_path}"
    return None
