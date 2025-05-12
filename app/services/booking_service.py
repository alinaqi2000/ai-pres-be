from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.models.booking_model import Booking
from database.models import Property, Unit
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
        return (
            db.query(Booking)
            .join(Property)
            .filter(Property.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_property(
        self, db: Session, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        return (
            db.query(Booking)
            .join(Booking.unit)
            .filter(Unit.property_id == property_id)
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
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
            Booking.start_date < end_date,
            Booking.end_date > start_date,
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        conflicting_booking = query.first()
        return conflicting_booking is None

    def create(
        self,
        db: Session,
        booking_in: BookingCreate,
        tenant_id: int,
        tenant_request_id: int,
    ) -> Optional[Booking]:
        unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
        if not unit:
            return None

        if not self.is_unit_available(
            db,
            booking_in.unit_id,
            booking_in.start_date,
            booking_in.end_date,
        ):
            return None

        db_booking = Booking(
            **booking_in.model_dump(exclude_none=True, exclude={"tenant_request_id"}),
            tenant_id=tenant_id,
            tenant_request_id=tenant_request_id,
            status=BookingStatus.PENDING,
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

    def update(
        self, db: Session, db_booking: Booking, booking_in: BookingUpdate
    ) -> Optional[Booking]:
        update_data = booking_in.model_dump(exclude_unset=True)

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
                return None

        for field, value in update_data.items():
            setattr(db_booking, field, value)

        db_booking.updated_at = datetime.now()
        db.commit()
        db.refresh(db_booking)
        return db_booking

    def delete(
        self, db: Session, booking_id: int, user_id: int, is_owner: bool
    ) -> bool:
        db_booking = self.get(db, booking_id)
        if not db_booking:
            return False

        can_delete = False
        if (
            db_booking.tenant_id == user_id
            and db_booking.status == BookingStatus.PENDING
        ):
            can_delete = True
        elif is_owner:
            can_delete = True

        if not can_delete:
            return False

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

        valid_transition = False
        if db_booking.status == BookingStatus.PENDING:
            if is_owner:
                if new_status == BookingStatus.CONFIRMED:
                    db_booking.status = new_status
                    valid_transition = True
                elif new_status == BookingStatus.REJECTED:
                    db_booking.status = new_status
                    valid_transition = True
            elif db_booking.tenant_id == user_id:
                if new_status == BookingStatus.CANCELLED_BY_TENANT:
                    db_booking.status = new_status
                    valid_transition = True

        elif db_booking.status == BookingStatus.CONFIRMED:
            if is_owner:
                if new_status == BookingStatus.ACTIVE:
                    db_booking.status = new_status
                    valid_transition = True
                elif new_status == BookingStatus.CANCELLED_BY_OWNER:
                    db_booking.status = new_status
                    valid_transition = True
            elif db_booking.tenant_id == user_id:
                if new_status == BookingStatus.CANCELLED_BY_TENANT:
                    db_booking.status = new_status
                    valid_transition = True

        elif db_booking.status == BookingStatus.ACTIVE:
            if is_owner:
                if new_status == BookingStatus.COMPLETED:
                    db_booking.status = new_status
                    valid_transition = True
                elif new_status == BookingStatus.CANCELLED_BY_OWNER:
                    db_booking.status = new_status
                    valid_transition = True

        if not valid_transition:
            return None

        db_booking.updated_at = datetime.now()
        db.commit()
        db.refresh(db_booking)
        return db_booking
