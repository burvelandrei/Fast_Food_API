import boto3
from sqlalchemy import select
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError
from botocore.config import Config
from db.connect import AsyncSessionLocal
from db.operations import ProductDO
from db.models import Product
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


def check_file_exists_to_s3(
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


def get_last_modified_to_s3(file_path: str):
    response = s3_client.head_object(
        Bucket=settings.S3_BACKET,
        Key=file_path,
    )
    last_modified = response["LastModified"]
    return last_modified


async def upload_to_s3(
    file_folder: str,
    file: UploadFile,
    model: Product,
    is_created: bool,
) -> str:
    """
    Загружает файл в S3, если файл для этого продукта существукт - удаляем его,
    если файл с таким именем уже есть у другого продукта - выбрасывем исключение
    """
    new_photo_name = file.filename
    file_path = f"{settings.STATIC_DIR}/{file_folder}/{new_photo_name}"
    file_exists = check_file_exists_to_s3(file_path)
    if file_exists:
        async with AsyncSessionLocal() as session:
            existing_product = await ProductDO.get_by_photo_name(
                photo_name=new_photo_name,
                session=session,
            )
        if existing_product and existing_product.id != model.id:
            raise HTTPException(
                status_code=400,
                detail="The file with this name already exists for another product!",
            )
    old_photo_name = None if is_created else model.photo_name
    if old_photo_name and old_photo_name != new_photo_name:
        await delete_from_s3(file_folder, old_photo_name)
    s3_client.upload_fileobj(
        file.file,
        settings.S3_BACKET,
        file_path,
        ExtraArgs={"ACL": "public-read"},
    )
    return new_photo_name


async def delete_from_s3(file_folder: str, file_name: str):
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
    """Получаем ссылку до файла в s3"""
    if not file_folder or not file_name:
        return None
    file_path = f"{settings.STATIC_DIR}/{file_folder}/{file_name}"
    if check_file_exists_to_s3(file_path=file_path):
        return f"{settings.S3_HOST}{settings.S3_BACKET}/{file_path}"
    return None
