from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.report_service import ReportService
from schemas.report_schema import (
    OwnerReportResponse,
    TenantReportResponse,
)
from utils.dependencies import get_db, get_current_user
from database.models.user_model import User
from responses.success import data_response

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)

@router.get("/owner", response_model=OwnerReportResponse)
async def get_owner_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get a dashboard report for a property owner.
    Only returns data for properties owned by the current user.
    """
    report_service = ReportService(db)
    report_data = report_service.get_owner_report(owner_id=current_user.id)
    return data_response(report_data)


@router.get("/tenant", response_model=TenantReportResponse)
async def get_tenant_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get a dashboard report for a tenant.
    Only returns data for bookings or requests belonging to the current user.
    """
    report_service = ReportService(db)
    report_data = report_service.get_tenant_report(tenant_id=current_user.id)
    return data_response(report_data)
