from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from database.init import get_db
from services.property_recommendation_service import PropertyRecommendationSystem
from services.email_service import EmailService
from database.models import Property as PropertyModel
from database.models import SearchHistory
from database.models.user_model import User

class BackgroundTasks:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.property_service = PropertyRecommendationSystem()
        self.email_service = EmailService()
        
        # Schedule the property recommendation task to run every minute
        self.scheduler.add_job(
            self.process_new_properties,
            'interval',
            minutes=1,
            id='property_recommendation_task'
        )
        
        print("Background tasks initialized and scheduled")

    async def process_new_properties(self):
        """Process new properties created in the last minute and send recommendations."""
        try:
            # Get a database session
            db = next(get_db())
            
            # Calculate time range for last minute
            one_minute_ago = datetime.now() - timedelta(minutes=1)
            
            # Get properties created in the last minute
            new_properties = db.query(PropertyModel).filter(
                PropertyModel.created_at >= one_minute_ago
            ).all()
            
            if not new_properties:
                print("No new properties found in the last minute")
                return
            
            print(f"Found {len(new_properties)} new properties to process")
            
            # Process each new property
            for property in new_properties:
                await self.process_property_recommendations(db, property)
                
        except Exception as e:
            print(f"Error in process_new_properties: {e}")

    async def process_property_recommendations(self, db: Session, property: PropertyModel):
        """Process recommendations for a single property."""
        try:
            # Convert property model to dictionary
            property_data = {
                'id': property.id,
                'name': property.name,
                'city': property.city,
                'monthly_rent': property.monthly_rent,
                'property_type': str(property.property_type),
                'description': property.description or '',
                'is_published': property.is_published
            }
            
            # Get users who should be notified
            users_to_notify = self.property_service.match_property_with_searches(property_data)
            
            if not users_to_notify:
                print(f"No users to notify for property {property.name}")
                return
            
            print(f"Found {len(users_to_notify)} users to notify for property {property.name}")
            
            # Send emails to each user
            for user_data in users_to_notify:
                user_id = user_data['id']
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.notification_preference:
                    # Get user's search history
                    search_history = db.query(SearchHistory).filter(
                        SearchHistory.user_id == user_id
                    ).order_by(SearchHistory.created_at.desc()).first()
                    
                    if search_history:
                        search_data = {
                            'query_name': search_history.query_name,
                            'query_city': search_history.query_city,
                            'monthly_rent_gt': search_history.monthly_rent_gt,
                            'monthly_rent_lt': search_history.monthly_rent_lt
                        }
                        
                        # Send recommendation email
                        await self.email_service.send_property_recommendation_email(
                            email=user.email,
                            property_data=property_data,
                            search_data=search_data
                        )
                        print(f"Sent recommendation email to user {user_id} for property {property.name}")
                    
        except Exception as e:
            print(f"Error processing recommendations for property {property.name}: {e}")
