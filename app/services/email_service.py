from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Union
from openai import AsyncOpenAI
from config import Settings

from database.models import Property, Unit, SearchHistory, User
import random
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



class PropertyMatchNotificationService:
    def __init__(self):
        self.email_service = EmailService()

    async def check_matches_and_notify(
        self, 
        db: Session, 
        item: Union[Property, Unit]
    ):
        """Check if new property/unit matches user searches and send notifications"""
        
        # Get monthly rent and city based on item type
        monthly_rent = item.monthly_rent
        city = item.city if isinstance(item, Property) else item.property.city
        
        # Find matching searches
        matching_searches = (
            db.query(SearchHistory)
            .filter(
                (SearchHistory.query_city == city)
                & (SearchHistory.monthly_rent_gt <= monthly_rent)
                & (SearchHistory.monthly_rent_lt >= monthly_rent)
            )
            .all()
        )

        # Group by user to avoid multiple emails
        for search in matching_searches:
            if not search.user_id or not search.user:
                continue
                
            user = search.user
            if not user.email:
                continue

            await self._send_match_notification(user, item, search)

    async def _send_match_notification(
        self, 
        user: User, 
        item: Union[Property, Unit], 
        search: SearchHistory
    ):
        """Generate and send AI-powered notification"""
        
        item_type = "property" if isinstance(item, Property) else "unit"
        name = item.name
        monthly_rent = item.monthly_rent
        city = item.city if isinstance(item, Property) else item.property.city

        prompt = f"""
        Write a friendly email about a new {item_type} matching these search criteria:
        - City: {search.query_city}
        - Budget: ${search.monthly_rent_gt} - ${search.monthly_rent_lt}

        {item_type.capitalize()} details:
        - Name: {name}
        - City: {city}
        - Monthly rent: ${monthly_rent}

        Keep it brief, personal and highlight the match with their search.
        """

        message = await self._generate_ai_message(prompt)
        
        await self.email_service.send_email(
            to_email=user.email,
            subject=f"New {item_type.capitalize()} Match Found: {name}",
            body=message
        )

    async def _generate_ai_message(self, prompt: str) -> str:
        """Generate personalized message using AI"""
        try:
            # Initialize OpenAI client
            settings = Settings()
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant writing friendly property match notifications."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback template if AI fails
            return f"We found a new listing matching your search criteria!\n\n{prompt}"