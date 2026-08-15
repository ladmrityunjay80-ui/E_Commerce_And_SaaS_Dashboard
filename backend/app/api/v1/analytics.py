from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.services.analytics import AnalyticsService
from app.api.deps import get_current_user
from app.models.user import User as UserModel
from app.core.rbac import has_permission

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_summary(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete dashboard summary (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    analytics_service = AnalyticsService(db)
    summary = analytics_service.get_dashboard_summary(date_from, date_to)
    return summary


@router.get("/financial-health")
async def get_financial_health(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial health metrics (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_financial_health(date_from, date_to)
    return metrics


@router.get("/subscriber-retention")
async def get_subscriber_retention(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscriber retention metrics (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_subscriber_retention(date_from, date_to)
    return metrics


@router.get("/customer-growth")
async def get_customer_growth(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer growth metrics (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_customer_growth(date_from, date_to)
    return metrics


@router.get("/revenue-by-period")
async def get_revenue_by_period(
    period: str = "monthly",
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get revenue breakdown by time period (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if period not in ["daily", "weekly", "monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Must be daily, weekly, monthly, or yearly")
    
    analytics_service = AnalyticsService(db)
    data = analytics_service.get_revenue_by_period(period, date_from, date_to)
    return data


@router.get("/top-products")
async def get_top_products(
    limit: int = 10,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top selling products (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if limit > 50:
        limit = 50  # Cap at 50
    
    analytics_service = AnalyticsService(db)
    products = analytics_service.get_top_products(limit, date_from, date_to)
    return products
