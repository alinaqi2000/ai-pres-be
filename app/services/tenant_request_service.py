from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from database.models import TenantRequest
from schemas.tenant_request_schema import TenantRequestCreate, TenantRequestUpdate
from services.booking_service import BookingService
from services.email_service import EmailService
from schemas.booking_schema import BookingCreate
from schemas.tenant_request_response import TenantRequestResponse
from utils.id_generator import generate_property_id, generate_unit_id
from datetime import datetime, timezone
from database.models.booking_model import Booking
from enums.tenant_request_status import TenantRequestStatus

class TenantRequestService:
    def __init__(self):
        self.model = TenantRequest
        self.booking_service = BookingService()
        self.email_service = EmailService()

    def create(self, db: Session, obj_in: TenantRequestCreate) -> TenantRequest:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def get(self, db: Session, request_id: int) -> Optional[TenantRequest]:
        return (
            db.query(TenantRequest)
            .options(
                joinedload(TenantRequest.tenant),
                joinedload(TenantRequest.property),
                joinedload(TenantRequest.floor),
                joinedload(TenantRequest.unit),
            )
            .filter(TenantRequest.id == request_id)
            .first()
        )

    def get_all(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return (
            db.query(TenantRequest)
            .options(
                joinedload(TenantRequest.tenant),
                joinedload(TenantRequest.property),
                joinedload(TenantRequest.floor),
                joinedload(TenantRequest.unit),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def check_existing_request(
        self, db: Session, tenant_id: int, request: TenantRequestCreate
    ) -> Optional[TenantRequest]:
        return (
            db.query(TenantRequest)
            .filter(
                TenantRequest.tenant_id == tenant_id,
                (
                    (TenantRequest.property_id == request.property_id)
                    & (TenantRequest.floor_id == request.floor_id)
                    & (TenantRequest.unit_id == request.unit_id)
                )
                | (
                    (TenantRequest.property_id == request.property_id)
                    & (TenantRequest.floor_id == request.floor_id)
                    & (TenantRequest.unit_id.is_(None))
                )
                | (
                    (TenantRequest.property_id == request.property_id)
                    & (TenantRequest.floor_id.is_(None))
                    & (TenantRequest.unit_id.is_(None))
                ),
            )
            .first()
        )

    def delete(self, db: Session, id: int) -> bool:
        db_obj = self.get(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False

    def get_by_property(
        self, db: Session, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return (
            db.query(self.model)
            .options(
                joinedload(self.model.tenant),
                joinedload(self.model.property),
                joinedload(self.model.floor),
                joinedload(self.model.unit),
            )
            .filter(self.model.property_id == property_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_tenant(
        self, db: Session, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return (
            db.query(self.model)
            .options(
                joinedload(self.model.tenant),
                joinedload(self.model.property),
                joinedload(self.model.floor),
                joinedload(self.model.unit),
            )
            .filter(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def update_status(self, db: Session, request_id: int, new_status: str, user_id: int) -> Optional[TenantRequest]:
        try:
            tenant_request = self.get(db, request_id)
            if not tenant_request:
                return None

            if new_status == TenantRequestStatus.ACCEPTED.value:
                tenant_request.status = new_status
                tenant_request.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(tenant_request)

                booking = self.booking_service.create_booking_from_tenant_request(
                    db=db,
                    tenant_request=tenant_request
                )
                
                if booking:
                    tenant = tenant_request.tenant
                    if tenant and tenant.email:
                        await self.email_service.send_update_action_email(
                            tenant.email,
                            "Tenant Request Status",
                            request_id
                        )
                        await self.email_service.send_create_action_email(
                            tenant.email,
                            "Booking",
                            booking.id
                        )
            elif new_status in [status.value for status in TenantRequestStatus]:
                tenant_request.status = new_status
                tenant_request.updated_at = datetime.now(timezone.utc)
                
                if new_status == TenantRequestStatus.REJECTED.value:
                    tenant = tenant_request.tenant
                    if tenant and tenant.email:
                        await self.email_service.send_update_action_email(
                            tenant.email,
                            "Tenant Request Status",
                            request_id
                        )
                
                db.commit()
                db.refresh(tenant_request)
            else:
                raise ValueError(f"Invalid status: {new_status}")

            return tenant_request

        except Exception as e:
            print(f"Error in update_status: {str(e)}")
            db.rollback()
            raise e

    def create_booking_from_tenant_request(
        self, db: Session, tenant_request: TenantRequest
    ) -> Optional[Booking]:
        try:
            booking_data = BookingCreate(
                tenant_id=tenant_request.tenant_id,
                property_id=tenant_request.property_id,
                floor_id=tenant_request.floor_id, 
                unit_id=tenant_request.unit_id,  
                start_date=tenant_request.start_date,
                end_date=tenant_request.end_date,
                monthly_offer=tenant_request.monthly_offer,
                status='pending',
                notes=f"Auto-created from tenant request {tenant_request.id}"
            )

            return self.booking_service.create(
                db=db,
                booking_in=booking_data,
                actual_tenant_id=tenant_request.tenant_id,
                booked_by_owner=False
            )
        except Exception as e:      
            print(f"Error creating booking: {str(e)}")
            return None

    def format_tenant_request_response(self, request: TenantRequest, db: Session) -> dict:
        response = TenantRequestResponse.model_validate(request)
        response_dict = response.model_dump()
        
        # Add IDs to both property and unit
        if "property" in response_dict and response_dict["property"]:
            response_dict["property"]["property_id"] = generate_property_id(response_dict["property"]["id"])
            
        if "unit" in response_dict and response_dict["unit"]:
            response_dict["unit"]["unit_id"] = generate_unit_id(response_dict["unit"]["id"])
            
        return response_dict
