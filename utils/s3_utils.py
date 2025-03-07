from environs import Env
import boto3
from botocore.exceptions import ClientError

env = Env()
env.read_env()


S3_HOST = env("S3_host")
S3_ACCESS_KEY = env("S3_ACCESS_KEY")
S3_SECRET_KEY = env("S3_SECRET_KEY")
S3_BACKET = env("S3_BACKET")


# Создаем клиент S3 с указанием ссылки на хранилище
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_HOST,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


def check_file_exists(
    key: str,
    bucket: str = S3_BACKET,
):
    """
    Проверяет существование файла в хранилище S3
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise
