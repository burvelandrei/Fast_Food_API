from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


# Функция для отправки письма для подтверждения почты
async def send_confirmation_email(email: str, token: str):
    confirm_url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/users/confirm-email/{token}/"
    message = MessageSchema(
        subject="Подтверждение почты",
        recipients=[email],
        body=f"Нажми на ссылку для подтверждения почты: {confirm_url}",
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
