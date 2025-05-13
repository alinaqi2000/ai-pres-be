from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from database.models.booking_model import Booking
from database.models import Property, Unit
from schemas.booking_schema import BookingCreate, BookingUpdate
from enums.booking_status import BookingStatus
from database.models.tenant_request_model import TenantRequest

class BookingService:
    def get(self, db: Session, booking_id: int) -> Optional[Booking]:
        return db.query(Booking).filter(Booking.id == booking_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
        return db.query(Booking).offset(skip).limit(limit).all()

    def get_by_tenant(
        self, db: Session, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        # tenant_id parameter here is actually a user_id
        return (
            db.query(Booking)
            .join(TenantRequest, TenantRequest.id == Booking.tenant_request_id, isouter=True)
            .filter(
                or_(
                    Booking.tenant_id == tenant_id, 
                    TenantRequest.tenant_id == tenant_id 
                )
            )
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
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
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
        actual_tenant_id: Optional[int],
        tenant_request_id: Optional[int],
        booked_by_owner: bool = False,
    ) -> Optional[Booking]:
        if booking_in.unit_id: 
            # 1. Fetch the Unit
            unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
            if not unit:
                print(f"ERROR: Unit {booking_in.unit_id} not found during booking creation for a specific unit.")
                return None
            if booking_in.property_id != unit.property_id: 
                print(f"ERROR: Provided property_id {booking_in.property_id} does not match unit's property_id {unit.property_id}.")
                return None 

            if not self.is_unit_available(db, booking_in.unit_id, booking_in.start_date, booking_in.end_date):
                print(f"INFO: Unit {booking_in.unit_id} is not available (general check failed).")
                return None

            if not booked_by_owner:
                conflicting_owner_booking = db.query(Booking).filter(
                    Booking.unit_id == booking_in.unit_id,
                    Booking.booked_by_owner == True,
                    Booking.tenant_id.isnot(None),
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
                    Booking.start_date < booking_in.end_date,
                    Booking.end_date > booking_in.start_date
                ).first()
                if conflicting_owner_booking:
                    print(f"INFO: Conflict for Unit {booking_in.unit_id} - already booked by owner for their tenant {conflicting_owner_booking.tenant_id}.")
                    return None
        else: 
            if not booking_in.property_id:
                print("ERROR: property_id must be provided for a whole property booking.")
                return None 
            property_units = db.query(Unit).filter(Unit.property_id == booking_in.property_id).all()
            if not property_units:
                print(f"INFO: No units found for property {booking_in.property_id} to book as a whole.")
                return None 

            for unit_in_prop in property_units:
                if not self.is_unit_available(db, unit_in_prop.id, booking_in.start_date, booking_in.end_date):
                    print(f"INFO: Unit {unit_in_prop.id} in property {booking_in.property_id} is not available (whole property booking check failed).")
                    return None
                
                if not booked_by_owner:
                    conflicting_owner_booking = db.query(Booking).filter(
                        Booking.unit_id == unit_in_prop.id,
                        Booking.booked_by_owner == True,
                        Booking.tenant_id.isnot(None),
                        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
                        Booking.start_date < booking_in.end_date,
                        Booking.end_date > booking_in.start_date
                    ).first()
                    if conflicting_owner_booking:
                        print(f"INFO: Conflict for Unit {unit_in_prop.id} in property {booking_in.property_id} - already booked by owner for their tenant {conflicting_owner_booking.tenant_id} (whole property booking check failed).")
                        return None
    
  
        db_booking = Booking(
            property_id=booking_in.property_id, 
            floor_id=booking_in.floor_id if booking_in.unit_id else None, 
            unit_id=booking_in.unit_id, 
            start_date=booking_in.start_date,
            end_date=booking_in.end_date,
            total_price=booking_in.total_price,
            notes=booking_in.notes,
            tenant_id=actual_tenant_id,
            tenant_request_id=tenant_request_id,
            booked_by_owner=booked_by_owner,
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
