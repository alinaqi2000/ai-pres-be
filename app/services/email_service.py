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
                VALIDATE_CERTS=False,
            )
            self.mailer = FastMail(self.config)
        except Exception as e:
            raise Exception(f"Failed to initialize email service: {str(e)}")

    async def send_new_password_email(self, email: str, new_password: str):
        message = MessageSchema(
            subject="🔐 Your New Password - Action Required",
            recipients=[email],
            body=f"""Hello,

Your password has been successfully reset. 

Your new password: {new_password}

For security reasons, please change this temporary password after logging in.

If you didn't request this password reset, please contact our support team immediately.

Best regards,
The Support Team""",
            subtype="plain",
        )
        await self.mailer.send_message(message)

    async def send_create_action_email(self, email: str, entity: str, entity_id: int):
        message = MessageSchema(
            subject=f"✅ {entity} Created Successfully - #{entity_id}",
            recipients=[email],
            body=f"""Hello,

Great news! Your new {entity.lower()} (ID: {entity_id}) has been created successfully.

You can now access and manage this {entity.lower()} from your dashboard. If you have any questions or need assistance, our support team is always ready to help.

Thank you for using our service!

Best regards,
The Support Team""",
            subtype="plain",
        )
        await self.mailer.send_message(message)

    async def send_update_action_email(self, email: str, entity: str, entity_id: int):
        message = MessageSchema(
            subject=f"🔄 {entity} Updated Successfully - #{entity_id}",
            recipients=[email],
            body=f"""Hello,

Your {entity.lower()} (ID: {entity_id}) has been updated successfully.

The changes you made have been saved and are now live. You can review these updates on your dashboard at any time.

If you did not make these changes or have any questions, please contact our support team.

Best regards,
The Support Team""",
            subtype="plain",
        )
        await self.mailer.send_message(message)

    async def send_delete_action_email(self, email: str, entity: str, entity_id: int):
        message = MessageSchema(
            subject=f"🗑️ {entity} Deleted Successfully - #{entity_id}",
            recipients=[email],
            body=f"""Hello,

Your {entity.lower()} (ID: {entity_id}) has been permanently deleted.

This action cannot be undone. If this deletion was made in error or you need assistance, please contact our support team within 30 days as recovery might be possible within this timeframe.

Thank you for using our service.

Best regards,
The Support Team""",
            subtype="plain",
        )
        await self.mailer.send_message(message)

    async def send_booking_email(
        self, email: str, property_id: int, booking_details=None
    ):
        if booking_details is None:
            booking_details = {}

        property_name = booking_details.get("property_name", f"Property #{property_id}")
        booking_date = booking_details.get("booking_date", "your selected dates")
        booking_ref = booking_details.get(
            "booking_ref", f"BK-{random.randint(10000, 99999)}"
        )

        message = MessageSchema(
            subject=f"🎉 Booking Confirmation: {property_name} - Ref: {booking_ref}",
            recipients=[email],
            body=f"""Hello,

Congratulations! Your booking for {property_name} has been confirmed.

Booking Details:
- Reference Number: {booking_ref}
- Property ID: {property_id}
- Dates: {booking_date}

Your reservation is now locked in. We've sent all the details to the property owner who will be expecting you.

Need to make changes? No problem! You can manage your booking through your account dashboard or contact our support team for assistance.

We hope you have a wonderful stay!

Best regards,
The Booking Team""",
            subtype="plain",
        )
        await self.mailer.send_message(message)
