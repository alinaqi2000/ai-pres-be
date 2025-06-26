from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class BookingStats(BaseModel):
    total: int = 0
    active: int = 0
    closed: int = 0

class PaymentStats(BaseModel):
    total_received: float = 0.0
    total_upcoming: float = 0.0

class TenantPaymentStats(BaseModel):
    total_given: float = 0.0
    total_upcoming: float = 0.0

class InvoiceStats(BaseModel):
    total_paid: int = 0
    total_overdue: int = 0

class BaseReportResponse(BaseModel):
    booking_stats: BookingStats
    payment_stats: PaymentStats
    invoice_stats: InvoiceStats
    generated_at: datetime
    
    class Config:
        from_attributes = True

# class AdminReportResponse(BaseReportResponse):
#     """Response model for admin summary report"""
#     pass

class OwnerReportResponse(BaseReportResponse):
    """Response model for owner dashboard report"""
    property_count: int = 0
    
    class Config:
        from_attributes = True

class TenantReportResponse(BaseReportResponse):
    """Response model for tenant dashboard report"""
    payment_stats: TenantPaymentStats

    """Response model for tenant dashboard report"""
    active_booking_count: int = 0
    
    class Config:
        from_attributes = True

# For backward compatibility
ReportResponse = OwnerReportResponse
