from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from database.models.booking_model import Booking
from database.models.payment_model import Payment
from database.models.invoice_model import Invoice
from database.models.property_model import Property
from database.models.user_model import User
from enums.booking_status import BookingStatus
from enums.invoice_status import InvoiceStatus
from enums.payment_status import PaymentStatus


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    # def get_summary_report(self):
    #     """
    #     Generate a summary report containing booking, payment, and invoice statistics.
    #     This is for admin users only.
    #     """
    #     # Get current time in UTC for the report generation timestamp
    #     report_time = datetime.now(timezone.utc)

    #     # Get booking statistics
    #     booking_stats = self._get_booking_stats()

    #     # Get payment statistics
    #     payment_stats = self._get_payment_stats()

    #     # Get invoice statistics
    #     invoice_stats = self._get_invoice_stats()

    #     return {
    #         "booking_stats": booking_stats,
    #         "payment_stats": payment_stats,
    #         "invoice_stats": invoice_stats,
    #         "generated_at": report_time,
    #     }

    def get_owner_report(self, owner_id: int) -> Dict[str, Any]:
        """
        Generate a report for a property owner.

        Args:
            owner_id: ID of the property owner

        Returns:
            Dict containing report data
        """
        # Get current time in UTC for the report generation timestamp
        report_time = datetime.now(timezone.utc)

        # Get properties owned by this owner
        properties = self.db.query(Property).filter(Property.owner_id == owner_id).all()
        property_ids = [p.id for p in properties]

        if not property_ids:
            return {
                "booking_stats": {"total": 0, "active": 0, "closed": 0},
                "payment_stats": {"total_received": 0.0, "total_upcoming": 0.0},
                "invoice_stats": {"total_paid": 0, "total_overdue": 0},
                "generated_at": report_time,
                "property_count": 0,
            }

        # Get booking statistics for owner's properties
        booking_stats = self._get_booking_stats(property_ids=property_ids)

        # Get payment statistics for owner's properties
        payment_stats = self._get_payment_stats(property_ids=property_ids)

        # Get invoice statistics for owner's properties
        invoice_stats = self._get_invoice_stats(property_ids=property_ids)

        return {
            "booking_stats": booking_stats,
            "payment_stats": payment_stats,
            "invoice_stats": invoice_stats,
            "generated_at": report_time,
            "property_count": len(property_ids),
        }

    def get_tenant_report(self, tenant_id: int) -> Dict[str, Any]:
        """
        Generate a report for a tenant.

        Args:
            tenant_id: ID of the tenant

        Returns:
            Dict containing report data
        """
        # Get current time in UTC for the report generation timestamp
        report_time = datetime.now(timezone.utc)

        # Get bookings for this tenant
        bookings = self.db.query(Booking).filter(Booking.tenant_id == tenant_id).all()
        booking_ids = [b.id for b in bookings]

        if not booking_ids:
            return {
                "booking_stats": {"total": 0, "active": 0, "closed": 0},
                "payment_stats": {"total_given": 0.0, "total_upcoming": 0.0},
                "invoice_stats": {"total_paid": 0, "total_overdue": 0},
                "generated_at": report_time,
                "active_booking_count": 0,
            }

        # Get booking statistics for tenant's bookings
        booking_stats = self._get_booking_stats(booking_ids=booking_ids)

        # Calculate total_given: sum of completed payments for tenant's bookings
        total_given_result = (
            self.db.query(func.sum(Payment.amount))
            .filter(Payment.booking_id.in_(booking_ids), Payment.status == PaymentStatus.COMPLETED)
            .first()
        )
        total_given = float(total_given_result[0]) if total_given_result[0] is not None else 0.0

        # Calculate total_upcoming: sum of unpaid invoice amounts for tenant's bookings
        unpaid_invoice_result = (
            self.db.query(func.sum(Invoice.amount))
            .filter(
                Invoice.booking_id.in_(booking_ids),
                Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE])
            )
            .first()
        )
        total_upcoming = float(unpaid_invoice_result[0]) if unpaid_invoice_result[0] is not None else 0.0

        payment_stats = {"total_given": round(total_given, 2), "total_upcoming": round(total_upcoming, 2)}

        # Get invoice statistics for tenant's bookings
        invoice_stats = self._get_invoice_stats(booking_ids=booking_ids)

        # Count active bookings
        active_bookings = sum(1 for b in bookings if b.status == BookingStatus.ACTIVE)

        return {
            "booking_stats": booking_stats,
            "payment_stats": payment_stats,
            "invoice_stats": invoice_stats,
            "generated_at": report_time,
            "active_booking_count": active_bookings,
        }

    def _get_booking_stats(
        self, property_ids: list[int] = None, booking_ids: list[int] = None
    ) -> Dict[str, int]:
        """
        Get statistics about bookings.

        Args:
            property_ids: Optional list of property IDs to filter by
            booking_ids: Optional list of booking IDs to filter by

        Returns:
            Dict containing booking statistics
        """
        query = self.db.query(Booking)

        # Apply filters if provided
        if property_ids is not None:
            query = query.filter(Booking.property_id.in_(property_ids))
        if booking_ids is not None:
            query = query.filter(Booking.id.in_(booking_ids))

        # Get total number of bookings
        total_bookings = query.count()

        # Get active bookings (status = 'active')
        active_bookings = query.filter(Booking.status == BookingStatus.ACTIVE).count()

        # Get closed bookings (status = 'closed')
        closed_bookings = query.filter(Booking.status == BookingStatus.CONFIRMED).count()

        return {
            "total": total_bookings,
            "active": active_bookings,
            "closed": closed_bookings,
        }

    def _get_payment_stats(
        self, property_ids: list[int] = None, booking_ids: list[int] = None
    ) -> Dict[str, float]:
        """
        Get statistics about payments.

        Args:
            property_ids: Optional list of property IDs to filter by
            booking_ids: Optional list of booking IDs to filter by

        Returns:
            Dict containing payment statistics
        """
        # Base query for completed payments
        completed_query = (
            self.db.query(func.sum(Payment.amount))
            .join(Booking, Payment.booking_id == Booking.id)
            .filter(Payment.status == PaymentStatus.COMPLETED)
        )

        # Base query for pending payments
        pending_query = (
            self.db.query(func.sum(Payment.amount))
            .join(Booking, Payment.booking_id == Booking.id)
            .filter(Payment.status == PaymentStatus.PENDING)
        )

        # Apply filters if provided
        if property_ids is not None:
            completed_query = completed_query.filter(
                Booking.property_id.in_(property_ids)
            )
            pending_query = pending_query.filter(Booking.property_id.in_(property_ids))
        if booking_ids is not None:
            completed_query = completed_query.filter(
                Payment.booking_id.in_(booking_ids)
            )
            pending_query = pending_query.filter(Payment.booking_id.in_(booking_ids))

        # Get total received amount (sum of all completed payments)
        total_received_result = completed_query.first()
        total_received = (
            float(total_received_result[0])
            if total_received_result[0] is not None
            else 0.0
        )

        # Get total upcoming amount (sum of all pending payments)
        total_upcoming_result = pending_query.first()
        total_upcoming = (
            float(total_upcoming_result[0])
            if total_upcoming_result[0] is not None
            else 0.0
        )

        return {
            "total_received": round(total_received, 2),
            "total_upcoming": round(total_upcoming, 2),
        }

    def _get_invoice_stats(
        self, property_ids: list[int] = None, booking_ids: list[int] = None
    ) -> Dict[str, int]:
        """
        Get statistics about invoices.

        Args:
            property_ids: Optional list of property IDs to filter by
            booking_ids: Optional list of booking IDs to filter by

        Returns:
            Dict containing invoice statistics
        """
        # Base query for paid invoices
        paid_query = self.db.query(Invoice).filter(Invoice.status == InvoiceStatus.PAID)

        # Base query for overdue invoices
        overdue_query = self.db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.OVERDUE
        )

        # Apply filters if provided
        if property_ids is not None or booking_ids is not None:
            # Join with bookings table if filtering by property or booking
            paid_query = paid_query.join(Booking, Invoice.booking_id == Booking.id)
            overdue_query = overdue_query.join(
                Booking, Invoice.booking_id == Booking.id
            )

            if property_ids is not None:
                paid_query = paid_query.filter(Booking.property_id.in_(property_ids))
                overdue_query = overdue_query.filter(
                    Booking.property_id.in_(property_ids)
                )

            if booking_ids is not None:
                paid_query = paid_query.filter(Invoice.booking_id.in_(booking_ids))
                overdue_query = overdue_query.filter(
                    Invoice.booking_id.in_(booking_ids)
                )

        # Get counts
        total_paid = paid_query.count()
        total_overdue = overdue_query.count()

        return {"total_paid": total_paid, "total_overdue": total_overdue}
