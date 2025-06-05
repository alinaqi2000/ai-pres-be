from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from database.models.booking_model import Booking
from database.models import Property, Unit, Floor
from database.models.user_model import User
from schemas.booking_schema import BookingCreate, BookingUpdate
from enums.booking_status import BookingStatus
from database.models.tenant_request_model import TenantRequest
from schemas.booking_response import BookingResponse
from schemas.property_response import (
    PropertyMinimumResponse,
    FloorMinimumResponse,
    UnitMinimumResponse,
)
from schemas.auth_schema import UserMinimumResponse
from utils.id_generator import generate_property_id, generate_unit_id
from services.invoice_service import InvoiceService
from services.email_service import EmailService
from responses.error import bad_request_error


class BookingService:
    def __init__(self):
        self.invoice_service = InvoiceService()
        self.email_service = EmailService()

    def get(self, db: Session, booking_id: int) -> Optional[Booking]:
        return db.query(Booking).filter(Booking.id == booking_id).first()

    def get_booking(self, db: Session, booking_id: int) -> Optional[Booking]:
        return self.get(db, booking_id)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
        return db.query(Booking).offset(skip).limit(limit).all()

    def get_by_tenant(self, db: Session, tenant_id: int) -> List[Booking]:
        """Get all bookings related to the specific tenant (both owner-created and tenant-requested)"""
        return db.query(Booking).filter(Booking.tenant_id == tenant_id).all()

    def get_my_bookings(self, db: Session, user_id: int) -> List[Booking]:
        """Get all bookings for properties owned by user"""
        owned_properties = db.query(Property).filter(Property.owner_id == user_id).all()
        property_ids = [p.id for p in owned_properties]
        return db.query(Booking).filter(Booking.property_id.in_(property_ids)).all()

    def get_by_property_owner(
        self, db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        """Get bookings for properties owned by this user but made by tenants (not the owner)"""
        return (
            db.query(Booking)
            .join(Property)
            .filter(Property.owner_id == owner_id)
            .filter(Booking.booked_by_owner == False)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_owner_created_bookings(self, db: Session, owner_id: int) -> List[Booking]:
        """Get only bookings created by owner for their own created tenants"""
        return (
            db.query(Booking)
            .join(Property)
            .filter(Property.owner_id == owner_id, Booking.booked_by_owner == True)
            .all()
        )

    def get_by_property(self, db: Session, property_id: int) -> List[Booking]:
        """Get all bookings for a property (both tenant requests and owner created)"""
        return db.query(Booking).filter(Booking.property_id == property_id).all()

    # def get_owner_property_bookings(self, db: Session, owner_id: int) -> List[Booking]:
    #     """Get all bookings for properties owned by the user"""
    #     return (
    #         db.query(Booking)
    #         .join(Property)
    #         .filter(Property.owner_id == owner_id)
    #         .all()
    #     )

    def get_by_unit(
        self, db: Session, unit_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        return (
            db.query(Booking)
            .filter(Booking.unit_id == unit_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def is_unit_available(
        self,
        db: Session,
        unit_id: int,
        start_date: datetime,
        end_date: datetime,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """Checks if the unit is available for the given period, excluding a specific booking (for updates)."""
        query = db.query(Booking).filter(
            Booking.unit_id == unit_id,
            Booking.status.in_(
                [BookingStatus.ACTIVE]
            ),
            end_date and Booking.start_date < end_date,
            end_date and Booking.end_date > start_date,
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        conflicting_booking = query.first()
        return conflicting_booking is None

    def is_property_occupied(
        self,
        db: Session,
        property_id: int,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """
        Check if any unit in the property is occupied during the given time period
        Returns True if occupied, False if available
        """
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            return False

        return property.is_occupied == True
        # Get all units for the property
        # units = db.query(Unit).filter(Unit.property_id == property_id).all()
        # if not units:
        #     return False

        # Check if any unit has a booking in the given time period
        # for unit in units:
        #     query = db.query(Booking).filter(
        #         Booking.unit_id == unit.id,
        #         Booking.status.in_(
        #             [
        #                 BookingStatus.ACTIVE,
        #             ]
        #         ),
        #         end_date and Booking.start_date < end_date,
        #         end_date and Booking.end_date > start_date,
        #     )

        #     if exclude_booking_id is not None:
        #         query = query.filter(Booking.id != exclude_booking_id)

        #     if query.first():
        #         return True

        # return False

    def is_property_fully_occupied(
        self, db: Session, property_id: int, start_date: datetime, end_date: datetime
    ) -> bool:
        """
        Check if all units in the property are occupied during the given time period
        Returns True if all units are occupied, False if any unit is available
        """
        # Get all units for the property
        units = db.query(Unit).filter(Unit.property_id == property_id).all()
        if not units:
            return False

        # Check each unit's availability
        for unit in units:
            if self.is_unit_available(db, unit.id, start_date, end_date):
                return False  # If any unit is available, property is not fully occupied

        return True

    def create(
        self,
        db: Session,
        booking_in: BookingCreate,
        actual_tenant_id: Optional[int],
        tenant_request_id: Optional[int] = None,
        booked_by_owner: bool = False,
    ) -> Optional[Booking]:

        # Add date validation
        current_date = datetime.now(timezone.utc)
        start_date = booking_in.start_date.replace(tzinfo=timezone.utc)

        if booking_in.end_date is not None:
            end_date = booking_in.end_date.replace(tzinfo=timezone.utc)
            min_duration = timedelta(days=30)
            if end_date - start_date < min_duration:
                return "Booking duration must be at least 30 days."
            status = (
                BookingStatus.CLOSED.value
                if end_date < current_date
                else BookingStatus.ACTIVE.value
            )
        else:
            status = BookingStatus.ACTIVE.value

        # For single unit booking
        if booking_in.unit_id:
            if not self.is_unit_available(
                db, booking_in.unit_id, booking_in.start_date, booking_in.end_date
            ):
                print(
                    f"INFO: Unit {booking_in.unit_id} is not available for the requested period"
                )
                return "Unit is not available for the requested period"
        # For whole property booking
        elif booking_in.property_id:
            if self.is_property_occupied(
                db, booking_in.property_id, booking_in.start_date, booking_in.end_date
            ):
                print(
                    f"INFO: Property {booking_in.property_id} has occupied units for the requested period"
                )
                return f"Property has occupied units for the requested period"

            if booked_by_owner and actual_tenant_id is not None:
                try:
                    self.check_existing_booking(
                        db, actual_tenant_id, booking_in.property_id
                    )
                except ValueError as e:
                    print(f"INFO: {str(e)}")
                    return str(e)
        else:
            print("ERROR: Neither unit_id nor property_id provided")
            return "Neither unit_id nor property_id provided"

        # Set the status before creating booking
        booking_in.status = status
        if booking_in.unit_id:
            unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
            booking_in.property_id = unit.property_id
            booking_in.floor_id = unit.floor_id
        
        # Create the booking
        booking = Booking(
            tenant_id=actual_tenant_id,
            property_id=booking_in.property_id,
            floor_id=booking_in.floor_id,
            unit_id=booking_in.unit_id,
            start_date=booking_in.start_date,
            end_date=booking_in.end_date,
            total_price=booking_in.total_price,
            notes=booking_in.notes,
            booked_by_owner=booked_by_owner,
            status=status,  # Add status here
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        if booking_in.unit_id:
            self.update_unit_occupancy(db, booking_in.unit_id, True)
        elif booking_in.property_id:
            self.update_property_occupancy(db, booking_in.property_id, True)

        return booking

    def update_unit_occupancy(self, db: Session, unit_id: int, is_occupied: bool):
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if unit:
            unit.is_occupied = is_occupied
            db.commit()

    def update_property_occupancy(
        self, db: Session, property_id: int, is_occupied: bool
    ):
        property = db.query(Property).filter(Property.id == property_id).first()
        if property:
            property.is_occupied = is_occupied
            db.commit()

    async def update(
        self, db: Session, booking_id: int, booking_in: BookingUpdate, is_owner: bool
    ) -> Optional[Booking]:
        """Update any booking field including status"""
        try:
            db_booking = self.get(db, booking_id)
            if not db_booking:
                return None

            update_data = booking_in.model_dump(exclude_unset=True)

            # Handle date changes
            if "start_date" in update_data or "end_date" in update_data:
                new_start = update_data.get("start_date", db_booking.start_date)
                new_end = update_data.get("end_date", db_booking.end_date)

                if db_booking.unit_id and not self.is_unit_available(
                    db,
                    db_booking.unit_id,
                    new_start,
                    new_end,
                    exclude_booking_id=booking_id,
                ):
                    print("Date update failed: Unit not available for selected dates")
                    return None

            if "status" in update_data:
                new_status = BookingStatus(update_data["status"])
                current_status = BookingStatus(db_booking.status)

                if (
                    not is_owner
                    or new_status != BookingStatus.ACTIVE
                ):
                    return None

                if new_status == BookingStatus.ACTIVE:
                    try:
                        invoice = self.invoice_service.create_invoice_from_booking(
                            db, db_booking
                        )
                        if not invoice:
                            return None

                        # Send invoice creation email to tenant
                        if db_booking.tenant and db_booking.tenant.email:
                            await self.email_service.send_create_action_email(
                                db_booking.tenant.email, "Invoice", invoice.id
                            )
                    except Exception as e:
                        print(f"Invoice creation failed: {str(e)}")
                        return None

            # Update all provided fields
            for field, value in update_data.items():
                setattr(db_booking, field, value)

            db_booking.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_booking)
            return db_booking

        except Exception as e:
            print(f"Update failed: {str(e)}")
            db.rollback()
            return None

    def delete(
        self, db: Session, booking_id: int, user_id: int, is_owner: bool
    ) -> bool:
        db_booking = self.get(db, booking_id)
        if not db_booking:
            return False

        can_delete = False
        if db_booking.tenant_id == user_id:
            can_delete = True
        elif is_owner:
            can_delete = True

        if not can_delete:
            return False

        db.delete(db_booking)
        db.commit()
        return True

    async def update_status(
        self,
        db: Session,
        booking_id: int,
        new_status: BookingStatus,
        user_id: int,
        is_owner: bool,
    ) -> Optional[Booking]:
        try:
            db_booking = self.get(db, booking_id)
            if not db_booking:
                return None

            if not is_owner:
                return None

            if new_status == BookingStatus.ACTIVE:
                db_booking.status = new_status.value
                db_booking.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(db_booking)

                tenant = db.query(User).filter(User.id == db_booking.tenant_id).first()
                if tenant and tenant.email:
                    await self.email_service.send_update_action_email(
                        tenant.email, "Booking Status", booking_id
                    )

                try:
                    invoice = self.invoice_service.create_invoice_from_booking(
                        db, db_booking
                    )
                    if not invoice:
                        db.rollback()
                        return None

                    tenant = (
                        db.query(User).filter(User.id == db_booking.tenant_id).first()
                    )
                    if tenant and tenant.email:
                        await self.email_service.send_create_action_email(
                            tenant.email, "Invoice", invoice.id
                        )
                except Exception as e:
                    db.rollback()
                    return None

                return db_booking

            return None

        except Exception as e:
            print(f"Error updating status: {str(e)}")
            db.rollback()
            return None

    def set_booking_response_data(
        self,
        response: BookingResponse,
        booking: Booking,
        db: Session,
        property_obj: Property = None,
    ):
        """Helper function to set property_id and owner data on booking responses"""
        if (
            hasattr(response, "property")
            and response.property
            and not response.property.property_id
        ):
            response.property.property_id = generate_property_id(response.property.id)

        if (
            response.tenant_request
            and hasattr(response.tenant_request, "property")
            and response.tenant_request.property
            and not response.tenant_request.property.property_id
        ):
            response.tenant_request.property.property_id = generate_property_id(
                response.tenant_request.property.id
            )

        if not property_obj:
            property_obj = (
                db.query(Property).filter(Property.id == booking.property_id).first()
            )

        if property_obj:
            owner_obj = db.query(User).filter(User.id == property_obj.owner_id).first()
            if owner_obj:
                response.owner = UserMinimumResponse.model_validate(owner_obj)

        return response

    def format_booking_response(
        self, booking: Booking, db: Session, property_obj: Property = None
    ) -> dict:
        response_dict = {}

        # Add required fields
        response_dict["id"] = booking.id
        response_dict["tenant"] = (
            UserMinimumResponse.model_validate(booking.tenant).model_dump()
            if booking.tenant
            else None
        )

        # Add property and owner info
        if not property_obj:
            property_obj = (
                db.query(Property).filter(Property.id == booking.property_id).first()
            )

        if property_obj:
            prop_response = PropertyMinimumResponse.model_validate(property_obj)
            prop_dict = prop_response.model_dump()
            prop_dict["property_id"] = generate_property_id(property_obj.id)
            response_dict["property"] = prop_dict

            # Add owner info
            owner = db.query(User).filter(User.id == property_obj.owner_id).first()
            response_dict["owner"] = (
                UserMinimumResponse.model_validate(owner).model_dump()
                if owner
                else None
            )

        # Add floor and unit info for tenant requests
        if not booking.booked_by_owner:
            if booking.floor:
                response_dict["floor"] = FloorMinimumResponse.model_validate(
                    booking.floor
                ).model_dump()

            if booking.unit:
                unit_response = UnitMinimumResponse.model_validate(booking.unit)
                unit_dict = unit_response.model_dump()
                unit_dict["unit_id"] = generate_unit_id(booking.unit.id)
                response_dict["unit"] = unit_dict

        response_dict["booked_by_owner"] = booking.booked_by_owner
        response_dict["status"] = booking.status
        response_dict["created_at"] = booking.created_at
        response_dict["start_date"] = booking.start_date
        response_dict["end_date"] = booking.end_date
        response_dict["updated_at"] = booking.updated_at
        response_dict["notes"] = booking.notes
        response_dict["total_price"] = booking.total_price

        return response_dict

    def validate_property_owner(
        self, db: Session, property_id: int, user_id: int
    ) -> Property:
        """Validate property exists and user is the owner"""
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            raise ValueError(f"Property with ID {property_id} not found.")
        if property_obj.owner_id != user_id:
            raise ValueError("You are not authorized to access this property.")
        return property_obj

    def validate_tenant_for_owner_booking(
        self, db: Session, tenant_id: int, owner_id: int
    ) -> User:
        """Validate tenant exists and was created by the owner"""
        tenant = db.query(User).filter(User.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"User with ID {tenant_id} not found.")
        if not tenant.booked_by_owner or tenant.created_by_owner_id != owner_id:
            raise ValueError(f"User ID {tenant_id} is not associated with you.")
        return tenant

    def check_existing_booking(self, db: Session, tenant_id: int, property_id: int):
        """Check if tenant already has a booking for this property"""
        existing = (
            db.query(Booking)
            .filter(
                Booking.tenant_id == tenant_id,
                Booking.property_id == property_id,
            )
            .first()
        )
        if existing:
            raise ValueError("Tenant already has a booking for this property.")

    def validate_booking_access(
        self, db: Session, booking: Booking, user_id: int
    ) -> tuple[bool, Optional[Property]]:
        """Validate if user has access to view/modify booking"""
        prop = db.query(Property).filter(Property.id == booking.property_id).first()
        is_owner = prop and prop.owner_id == user_id

        is_tenant_via_request = False
        if booking.tenant_request_id:
            tenant_request = (
                db.query(TenantRequest)
                .filter(TenantRequest.id == booking.tenant_request_id)
                .first()
            )
            if tenant_request and tenant_request.tenant_id == user_id:
                is_tenant_via_request = True

        has_access = (booking.tenant_id == user_id) or is_tenant_via_request or is_owner
        return has_access, prop

    def validate_unit_and_floor(
        self, db: Session, unit_id: int, floor_id: int, property_id: int
    ) -> bool:
        """Validate unit and floor belong to property"""
        unit = (
            db.query(Unit)
            .filter(Unit.id == unit_id, Unit.property_id == property_id)
            .first()
        )

        floor = (
            db.query(Floor)
            .filter(Floor.id == floor_id, Floor.property_id == property_id)
            .first()
        )

        return bool(unit and floor and unit.floor_id == floor.id)

    def get_property_from_unit(self, db: Session, unit_id: int) -> Optional[Property]:
        """Get property details from unit ID"""
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            return None

        floor = db.query(Floor).filter(Floor.id == unit.floor_id).first()
        if not floor:
            return None

        return db.query(Property).filter(Property.id == floor.property_id).first()

    def is_property_owner(self, db: Session, user_id: int) -> bool:
        """Check if user owns any properties"""
        return (
            db.query(Property).filter(Property.owner_id == user_id).first() is not None
        )

    def create_booking_from_tenant_request(
        self, db: Session, tenant_request: TenantRequest
    ) -> Optional[Booking]:
        """Create a booking automatically from an accepted tenant request"""
        try:
            print(f"Creating booking for tenant request {tenant_request.id}")

            booking_data = BookingCreate(
                tenant_id=tenant_request.tenant_id,
                property_id=tenant_request.property_id,
                floor_id=tenant_request.floor_id,
                unit_id=tenant_request.unit_id,
                start_date=tenant_request.start_date,
                end_date=tenant_request.end_date,
                total_price=tenant_request.monthly_offer,
                status="pending",
                notes=f"Auto-created from tenant request {tenant_request.id}",
            )

            return self.create(
                db=db,
                booking_in=booking_data,
                actual_tenant_id=tenant_request.tenant_id,
                tenant_request_id=tenant_request.id,
                booked_by_owner=False,
            )
        except Exception as e:
            print(
                f"Error creating booking from tenant request {tenant_request.id}: {str(e)}"
            )
            return None

    def is_property_already_booked(self, db: Session, property_id: int) -> bool:
        """Check if property has any active bookings"""
        return (
            db.query(Booking)
            .filter(
                Booking.property_id == property_id,
                Booking.status.in_(
                    [
                        BookingStatus.ACTIVE,
                    ]
                ),
            )
            .first()
            is not None
        )
