import boto3
import logging
import logging.config
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError
from botocore.config import Config
from db.connect import AsyncSessionLocal
from db.operations import ProductDO
from db.models import Product
from utils.logger import logging_config
from config import settings


logging.config.dictConfig(logging_config)
logger = logging.getLogger("s3")


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
        logger.info(f"File found in S3: {file_path}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            logger.info(f"File not found in S3: {file_path}")
            return False
        else:
            logger.error(
                f"Error checking file in S3: {file_path}, {e}",
                exc_info=True,
            )
            raise e


def get_last_modified_to_s3(file_path: str):
    try:
        response = s3_client.head_object(
            Bucket=settings.S3_BACKET,
            Key=file_path,
        )
        last_modified = response["LastModified"]
        return last_modified
    except ClientError as e:
        logger.error(
            f"Error getting last modified date for {file_path}: {e}",
            exc_info=True,
        )
        raise e


async def upload_to_s3(
    file_folder: str,
    file: UploadFile,
    model: Product,
    is_created: bool,
) -> str:
    """
    Загружает файл в S3,
    если файл для этого продукта существует - удаляем его,
    если файл с таким именем уже есть
    у другого продукта - выбрасывем исключение
    """
    new_file_name = file.filename
    file_path = f"{settings.STATIC_DIR}/{file_folder}/{new_file_name}"
    logger.info(f"Uploading file to S3: {file_path}")
    file_exists = check_file_exists_to_s3(file_path)
    if file_exists:
        async with AsyncSessionLocal() as session:
            existing_product = await ProductDO.get_by_photo_name(
                photo_name=new_file_name,
                session=session,
            )
        if existing_product and existing_product.id != model.id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The file with this name already exists for "
                    "another product!"
                )
            )
    old_file_name = None if is_created else model.photo_name
    if old_file_name and old_file_name != new_file_name:
        await delete_from_s3(file_folder, old_file_name)
    try:
        s3_client.upload_fileobj(
            file.file,
            settings.S3_BACKET,
            file_path,
            ExtraArgs={"ACL": "public-read"},
        )
        logger.info(f"File uploaded successfully: {file_path}")
        return new_file_name
    except Exception as e:
        logger.error(
            f"Failed to upload file {file_path}: {e}",
            exc_info=True,
        )
        raise e


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
        logger.info(f"File deleted from S3: {file_path}")
    except Exception as e:
        logger.error(
            f"Failed to delete file {file_path}: {e}",
            exc_info=True,
        )
        raise e


def get_s3_url(file_folder: str, file_name: str):
    """Получаем ссылку до файла в s3"""
    if not file_folder or not file_name:
        return None
    file_path = f"{settings.STATIC_DIR}/{file_folder}/{file_name}"
    last_modifed = get_last_modified_to_s3(file_path=file_path)
    if check_file_exists_to_s3(file_path=file_path):
        file_url = f"/{file_path}?{last_modifed}"
        return f"{settings.S3_HOST}{settings.S3_BACKET}{file_url}"
    logger.warning(f"File not found in S3, cannot generate URL: {file_path}")
    return None
