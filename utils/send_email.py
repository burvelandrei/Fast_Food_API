from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from environs import Env


env = Env()
env.read_env()

conf = ConnectionConfig(
    MAIL_USERNAME=env("MAIL_USERNAME"),
    MAIL_PASSWORD=env("MAIL_PASSWORD"),
    MAIL_FROM=env("MAIL_FROM"),
    MAIL_PORT=int(env("MAIL_PORT")),
    MAIL_SERVER=env("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


# Функция для отправки письма для подтверждения почты
async def send_confirmation_email(email: str, token: str):
    confirm_url = (
        f"http://{env("SERVER_HOST")}:{env("SERVER_PORT")}/users/confirm-email/{token}/"
    )
    message = MessageSchema(
        subject="Подтверждение почты",
        recipients=[email],
        body=f"Нажми на ссылку для подтверждения почты: {confirm_url}",
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
