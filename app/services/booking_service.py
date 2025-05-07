from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.models.booking_model import Booking
from database.models.property_model import Property, Unit
from schemas.booking_schema import BookingCreate, BookingUpdate
from enums.booking_status import BookingStatus


class BookingService:
    def get(self, db: Session, booking_id: int) -> Optional[Booking]:
        return db.query(Booking).filter(Booking.id == booking_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
        return db.query(Booking).offset(skip).limit(limit).all()

    def get_by_tenant(
        self, db: Session, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        return (
            db.query(Booking)
            .filter(Booking.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_property_owner(
        self, db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        # This requires joining Booking with Property to filter by owner_id
        return (
            db.query(Booking)
            .join(Property)
            .filter(Property.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

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
                [BookingStatus.CONFIRMED, BookingStatus.ACTIVE]
            ),  # Consider only confirmed/active bookings for conflicts
            Booking.start_date
            < end_date,  # New booking starts before existing one ends
            Booking.end_date > start_date,  # New booking ends after existing one starts
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        conflicting_booking = query.first()
        return conflicting_booking is None

    def create(
        self, db: Session, booking_in: BookingCreate, tenant_id: int
    ) -> Optional[Booking]:
        # 1. Check if unit exists and is not generally marked as unavailable/occupied indefinitely
        unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
        if not unit:
            # This case should ideally be caught by a route dependency or earlier check
            return None  # Or raise an exception: raise ValueError("Unit not found")
        if unit.is_occupied:  # General flag on the unit model itself
            # Or raise an exception: raise ValueError("Unit is already occupied")
            return None

        # 2. Check for booking conflicts
        if not self.is_unit_available(
            db, booking_in.unit_id, booking_in.start_date, booking_in.end_date
        ):
            # Or raise an exception: raise ValueError("Unit is not available for the selected dates")
            return None

        # 3. Prevent tenant from booking the same unit for overlapping periods if desired (optional)
        # existing_tenant_booking = db.query(Booking).filter(
        #     Booking.tenant_id == tenant_id,
        #     Booking.unit_id == booking_in.unit_id,
        #     Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
        #     Booking.start_date < booking_in.end_date,
        #     Booking.end_date > booking_in.start_date
        # ).first()
        # if existing_tenant_booking:
        #     return None # Or raise an exception: raise ValueError("Tenant already has an overlapping booking for this unit")

        db_booking = Booking(
            **booking_in.model_dump(),
            tenant_id=tenant_id,
            status=BookingStatus.PENDING  # Initial status
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

    def update(
        self, db: Session, db_booking: Booking, booking_in: BookingUpdate
    ) -> Optional[Booking]:
        update_data = booking_in.model_dump(exclude_unset=True)

        # If dates are being changed, check for availability
        new_start_date = update_data.get("start_date", db_booking.start_date)
        new_end_date = update_data.get("end_date", db_booking.end_date)

        if (
            new_start_date != db_booking.start_date
            or new_end_date != db_booking.end_date
        ):
            if not self.is_unit_available(
                db,
                db_booking.unit_id,
                new_start_date,
                new_end_date,
                exclude_booking_id=db_booking.id,
            ):
                return None  # Or raise an exception

        for field, value in update_data.items():
            setattr(db_booking, field, value)

        db_booking.updated_at = (
            datetime.utcnow()
        )  # Manually update timestamp if not auto by DB trigger
        db.commit()
        db.refresh(db_booking)
        return db_booking

    def delete(
        self, db: Session, booking_id: int, user_id: int, is_owner: bool
    ) -> bool:
        db_booking = self.get(db, booking_id)
        if not db_booking:
            return False

        # Logic for who can delete (e.g., tenant can cancel PENDING, owner can cancel almost anytime)
        can_delete = False
        if (
            db_booking.tenant_id == user_id
            and db_booking.status == BookingStatus.PENDING
        ):
            can_delete = True
            # Optionally change status to CANCELLED_BY_TENANT instead of hard delete
            # db_booking.status = BookingStatus.CANCELLED_BY_TENANT
            # db.commit()
            # return True
        elif is_owner:  # Add more granular checks for owner if needed
            can_delete = True
            # Optionally change status to CANCELLED_BY_OWNER
            # db_booking.status = BookingStatus.CANCELLED_BY_OWNER
            # db.commit()
            # return True

        if not can_delete:
            return False  # Or raise a permission error

        db.delete(db_booking)
        db.commit()
        return True

    def update_status(
        self,
        db: Session,
        booking_id: int,
        new_status: BookingStatus,
        user_id: int,
        is_owner: bool,
    ) -> Optional[Booking]:
        """Allows updating the booking status, e.g., by an owner or system process."""
        db_booking = self.get(db, booking_id)
        if not db_booking:
            return None

        # Authorization: Who can change to what status?
        # Example: Owner can confirm a PENDING booking
        if (
            is_owner
            and db_booking.status == BookingStatus.PENDING
            and new_status == BookingStatus.CONFIRMED
        ):
            # Additional logic for CONFIRMED: mark unit as occupied if applicable by your design
            # unit = db.query(Unit).filter(Unit.id == db_booking.unit_id).first()
            # if unit:
            #     unit.is_occupied = True # This needs careful consideration: when does it become unoccupied?
            db_booking.status = new_status
        elif (
            db_booking.tenant_id == user_id
            and db_booking.status == BookingStatus.PENDING
            and new_status == BookingStatus.CANCELLED_BY_TENANT
        ):
            db_booking.status = new_status
        # Add more status transition logic as needed...
        else:
            # Invalid status transition or permission denied
            return None  # Or raise an error

        db_booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_booking)
        return db_booking
