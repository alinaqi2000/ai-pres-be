from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from services.report_service import ReportService
from schemas.report_schema import (
    # AdminReportResponse,
    OwnerReportResponse,
    TenantReportResponse,
)
from utils.dependencies import get_db, get_current_user
from database.models.user_model import User
from responses.success import data_response
from responses.error import forbidden_error, bad_request_error

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)


# @router.get("/summary", response_model=AdminReportResponse)
# async def get_summary_report(
#     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
# ):
#     """
#     Get a summary report containing booking, payment, and invoice statistics.

#     This endpoint is restricted to admin users only.

#     Returns:
#         ReportResponse: A summary report with various statistics
#     """
#     # Check if user is admin
#     if current_user.role != UserRole.ADMIN:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=forbidden_error("Only admin users can access this report"),
#         )

#     # Generate and return the report
#     report_service = ReportService(db)
#     report_data = report_service.get_summary_report()
#     return data_response(report_data)


@router.get("/owner", response_model=OwnerReportResponse)
async def get_owner_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get a dashboard report for a property owner.
    Only returns data for properties owned by the current user.
    """
    # Check if the user owns any property
    from database.models.property_model import Property

    is_owner = db.query(Property).filter(Property.owner_id == current_user.id).first()
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=forbidden_error("Only property owners can access this report"),
        )
    report_service = ReportService(db)
    report_data = report_service.get_owner_report(owner_id=current_user.id)
    return data_response(report_data)


@router.get("/tenant")
async def get_tenant_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get a dashboard report for a tenant.
    Only returns data for bookings or requests belonging to the current user.
    """
    from database.models.booking_model import Booking
    from database.models.tenant_request_model import TenantRequest

    is_tenant = (
        db.query(Booking).filter(Booking.tenant_id == current_user.id).first()
        or db.query(TenantRequest)
        .filter(TenantRequest.tenant_id == current_user.id)
        .first()
    )
    if not is_tenant:
        return bad_request_error("You must be a tenant to access this report")
    report_service = ReportService(db)
    report_data = report_service.get_tenant_report(tenant_id=current_user.id)
    return data_response(report_data)
