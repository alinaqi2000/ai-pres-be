from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from database.models.booking_model import Booking
from database.models import Property, Unit
from database.models.user_model import User
from schemas.booking_schema import BookingCreate, BookingUpdate
from enums.booking_status import BookingStatus
from database.models.tenant_request_model import TenantRequest


class BookingService:
    def get(self, db: Session, booking_id: int) -> Optional[Booking]:
        return db.query(Booking).filter(Booking.id == booking_id).first()

    def get_booking(self, db: Session, booking_id: int) -> Optional[Booking]:
        return self.get(db, booking_id)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
        return db.query(Booking).offset(skip).limit(limit).all()

    def get_by_tenant(
        self, db: Session, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        """Get bookings where this user is the tenant"""
        return (
            db.query(Booking)
            .join(
                TenantRequest,
                TenantRequest.id == Booking.tenant_request_id,
                isouter=True,
            )
            .filter(
                or_(
                    Booking.tenant_id == tenant_id, TenantRequest.tenant_id == tenant_id
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_my_bookings(self, db: Session, tenant_id: int) -> List[Booking]:
        return self.get_by_tenant(db, tenant_id)

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

    def get_owner_created_bookings(
        self, db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        """Get bookings that were created by the property owner for their own tenants"""
        return (
            db.query(Booking)
            .join(Property)
            .filter(Property.owner_id == owner_id)
            .filter(Booking.booked_by_owner == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_property_owner_bookings(self, db: Session, owner_id: int) -> List[Booking]:
        return self.get_owner_created_bookings(db, owner_id)

    def get_by_property(
        self, db: Session, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        """Get bookings for a specific property"""
        return (
            db.query(Booking)
            .join(Booking.unit)
            .filter(Unit.property_id == property_id)
            .filter(Booking.booked_by_owner == False)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_bookings_for_property(self, db: Session, property_id: int) -> List[Booking]:
        return self.get_by_property(db, property_id)

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
                [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.ACTIVE]
            ),
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
        tenant_request_id: Optional[int] = None,
        booked_by_owner: bool = False,
    ) -> Optional[Booking]:
        if booking_in.unit_id:
            unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
            if not unit:
                return None
            existing_booking = (
                db.query(Booking)
                .filter(
                    Booking.unit_id == booking_in.unit_id,
                    Booking.start_date < booking_in.end_date,
                    Booking.end_date > booking_in.start_date,
                )
                .first()
            )
            if existing_booking:
                print(
                    f"INFO: Unit {booking_in.unit_id} is already booked by owner for tenant {existing_booking.tenant_id}"
                )
                return None
        else:
            if not booking_in.property_id:
                print(
                    "ERROR: property_id must be provided for a whole property booking."
                )
                return None
            property_units = (
                db.query(Unit).filter(Unit.property_id == booking_in.property_id).all()
            )
            if not property_units:
                print(
                    f"INFO: No units found for property {booking_in.property_id} to book as a whole."
                )
                return None

            if booked_by_owner and actual_tenant_id:
                duplicate_tenant_booking = (
                    db.query(Booking)
                    .filter(
                        Booking.property_id == booking_in.property_id,
                        Booking.tenant_id == actual_tenant_id,
                        Booking.booked_by_owner == True,
                        Booking.status.in_(
                            [
                                BookingStatus.PENDING,
                                BookingStatus.CONFIRMED,
                                BookingStatus.ACTIVE,
                            ]
                        ),
                        Booking.start_date < booking_in.end_date,
                        Booking.end_date > booking_in.start_date,
                    )
                    .first()
                )
                if duplicate_tenant_booking:
                    print(
                        f"INFO: A booking already exists for tenant {actual_tenant_id} during this time period"
                    )
                    return None

            for unit_in_prop in property_units:
                existing_booking = (
                    db.query(Booking)
                    .filter(
                        Booking.unit_id == unit_in_prop.id,
                        Booking.status.in_(
                            [
                                BookingStatus.PENDING,
                                BookingStatus.CONFIRMED,
                                BookingStatus.ACTIVE,
                            ]
                        ),
                        Booking.start_date < booking_in.end_date,
                        Booking.end_date > booking_in.start_date,
                    )
                    .first()
                )
                if existing_booking:
                    print(
                        f"INFO: Unit {unit_in_prop.id} in property {booking_in.property_id} is already booked"
                    )
                    return None

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
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    def update(
        self, db: Session, db_booking: Booking, booking_in: BookingUpdate
    ) -> Optional[Booking]:
        """Update a booking"""
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

    def update_booking(
        self, db: Session, booking_id: int, booking_in: BookingUpdate
    ) -> Optional[Booking]:
        db_booking = self.get(db, booking_id)
        if not db_booking:
            return None
        return self.update(db, db_booking, booking_in)

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
