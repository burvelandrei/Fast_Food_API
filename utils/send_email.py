import logging
import logging.config
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from utils.logger import logging_config
from config import settings


logging.config.dictConfig(logging_config)
logger = logging.getLogger("send_email")


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


async def send_confirmation_email(email: str, token: str):
    """Функция отправки письма подтверждения почты"""
    confirm_url = (
        f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/"
        f"users/confirm-email/{token}/"
    )
    email_header = "<html><body><h3>Подтверждение электронной почты</h3>"
    email_main_text = (
        "<p>Спасибо за регистрацию! Для завершения процесса, пожалуйста, "
        "подтвердите ваш email, нажав на ссылку ниже:</p>"
    )
    email_link = f'<p><a href="{confirm_url}">{confirm_url}</a></p>'
    email_warning = (
        '<p style="color: #ff0000; font-weight: bold;">'
        "Внимание: Если вы не регистрировались в нашем сервисе, "
        "пожалуйста, не переходите по ссылке и проигнорируйте это письмо.</p>"
    )
    email_footer = "</body></html>"

    email_body = (
        email_header
        + email_main_text
        + email_link
        + email_warning
        + email_footer
    )

    message = MessageSchema(
        subject="Подтверждение электронной почты",
        recipients=[email],
        body=email_body,
        subtype="html",
    )
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info("Confirmation email successfully sent")
    except Exception as e:
        logger.error(
            f"Failed to send confirmation email {e}",
            exc_info=True,
        )
