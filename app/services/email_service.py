from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config import EMAIL_FROM, EMAIL_FROM_NAME, EMAIL_PORT, EMAIL_SERVER, OPENAI_API_KEY
import openai


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

    async def send_email(self, to_email: str, subject: str, body: str):
        """Send a generic email"""
        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=body,
            subtype="plain",
        )
        await self.mailer.send_message(message)

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

    async def send_create_action_email(
        self, 
        email: str, 
        entity_type: str, 
        entity_id: int, 
        additional_message: str = None
    ):
        """Send email notification for entity creation"""
        subject = f"New {entity_type} Created"
        content = f"A new {entity_type} with ID {entity_id} has been created."
        
        if additional_message:
            content += f"\n\n{additional_message}"
            
        await self.send_email(email, subject, content)

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

    async def send_property_recommendation_email(self, email: str, property_data: dict, search_data: dict):
        """
        Generate and send a personalized email about a new property matching user's search history.
        
        Args:
            email: Recipient's email address
            property_data: Dictionary containing property information
            search_data: Dictionary containing user's search history
        """
        # Configure OpenAI
        openai.api_key = OPENAI_API_KEY
        
        # Create a prompt for generating a personalized email
        prompt = f"""Write a personalized and engaging email to a potential buyer about a new property listing.
        
        Property Details:
        Name: {property_data.get('name', 'Unnamed Property')}
        City: {property_data.get('city', '')}
        Monthly Rent: ${property_data.get('monthly_rent', 0)}
        Type: {property_data.get('property_type', 'Unknown')}
        Description: {property_data.get('description', '')}
        
        User's Search Preferences:
        Search Query: {search_data.get('query_name', '')}
        Preferred City: {search_data.get('query_city', '')}
        Price Range: ${search_data.get('monthly_rent_gt', 0)} - ${search_data.get('monthly_rent_lt', 'any')}
        
        Generate a catchy subject line and a personalized email body that:
        1. Highlights the property's key features
        2. Emphasizes how it matches the user's search preferences
        3. Creates urgency while being professional
        4. Includes a clear call-to-action
        5. Is concise but informative
        """
        
        try:
            # Generate email content using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional real estate email copywriter. Write engaging, personalized emails that convert leads into customers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract generated content
            content = response.choices[0].message.content
            
            # Parse the response to get subject and body
            subject_start = content.find("Subject:")
            body_start = content.find("Body:")
            
            if subject_start != -1 and body_start != -1:
                subject = content[subject_start + len("Subject:"):body_start].strip()
                body = content[body_start + len("Body:"):].strip()
            else:
                # Fallback to default format if OpenAI response doesn't match expected structure
                subject = f"✨ New Property Alert: {property_data.get('name', 'Your Dream Home')} in {property_data.get('city', 'Your City')}"
                body = f"""Dear Home Seeker,

We're excited to inform you that we've found a property that matches your search preferences!

Property: {property_data.get('name', 'Your Dream Home')}
Location: {property_data.get('city', 'Your City')}
Monthly Rent: ${property_data.get('monthly_rent', 0)}

This property aligns perfectly with your search criteria:
- City: {search_data.get('query_city', '')}
- Price Range: ${search_data.get('monthly_rent_gt', 0)} - ${search_data.get('monthly_rent_lt', 'any')}

Would you like to learn more about this opportunity? Don't miss out on your perfect home!

Best regards,
Your Real Estate Team"""
            
            # Create and send the email
            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=body,
                subtype="plain",
            )
            await self.mailer.send_message(message)
            
        except Exception as e:
            print(f"Error generating or sending recommendation email: {e}")
            # Fallback to default email if OpenAI fails
            message = MessageSchema(
                subject=f"✨ New Property Alert: {property_data.get('name', 'Your Dream Home')} in {property_data.get('city', 'Your City')}",
                recipients=[email],
                body=f"""Dear Home Seeker,

We've found a property that matches your search preferences!

Property: {property_data.get('name', 'Your Dream Home')}
Location: {property_data.get('city', 'Your City')}
Monthly Rent: ${property_data.get('monthly_rent', 0)}

This property aligns perfectly with your search criteria:
- City: {search_data.get('query_city', '')}
- Price Range: ${search_data.get('monthly_rent_gt', 0)} - ${search_data.get('monthly_rent_lt', 'any')}

Would you like to learn more about this opportunity? Don't miss out on your perfect home!

Best regards,
Your Real Estate Team""",
                subtype="plain",
            )
            await self.mailer.send_message(message)


