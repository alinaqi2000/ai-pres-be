from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import random
import string
from config import EMAIL_FROM, EMAIL_FROM_NAME, EMAIL_PORT, EMAIL_SERVER

class EmailService:
    def __init__(self):
        try:
            self.config = ConnectionConfig(
                MAIL_USERNAME="",
                MAIL_PASSWORD="",
                MAIL_FROM=EMAIL_FROM,
                MAIL_PORT=EMAIL_PORT,
                MAIL_SERVER=EMAIL_SERVER,
                MAIL_FROM_NAME=EMAIL_FROM_NAME,
                MAIL_STARTTLS=False,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=False,
                VALIDATE_CERTS=False
            )
            self.mailer = FastMail(self.config)
        except Exception as e:
            raise Exception(f"Failed to initialize email service: {str(e)}")

    async def send_new_password_email(self, email: str, new_password: str):
        message = MessageSchema(
            subject="Password Reset - New Password",
            recipients=[email],
            body=f"Your password has been reset. Here is your new password:\n\n{new_password}\n\nPlease change it after logging in.",
            subtype="plain"
        )
        
        await self.mailer.send_message(message)

    def _generate_password(self) -> str:
        """Generate an 8-character alphanumeric password"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))
