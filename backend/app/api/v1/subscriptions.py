from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.schemas.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate, SubscriptionFilter, Plan, PlanCreate, PlanUpdate
from app.services.subscription import SubscriptionService, PlanService
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User as UserModel
from app.core.rbac import has_permission

router = APIRouter()


# Subscription endpoints
@router.get("", response_model=List[Subscription])
async def get_subscriptions(
    search: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscriptions with filtering (requires subscriptions:read permission)."""
    if not has_permission(current_user, "subscriptions:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    filters = SubscriptionFilter(
        search=search,
        status=status,
        customer_id=customer_id,
        plan_id=plan_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )
    subscriptions = subscription_service.get_subscriptions(filters)
    return subscriptions


@router.get("/statistics")
async def get_subscription_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription statistics (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    stats = subscription_service.get_subscription_statistics(date_from, date_to)
    return stats


@router.get("/{subscription_id}", response_model=Subscription)
async def get_subscription(
    subscription_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription by ID (requires subscriptions:read permission)."""
    if not has_permission(current_user, "subscriptions:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.post("", response_model=Subscription, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new subscription (requires subscriptions:create permission)."""
    if not has_permission(current_user, "subscriptions:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    try:
        subscription = subscription_service.create_subscription(subscription_data)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{subscription_id}", response_model=Subscription)
async def update_subscription(
    subscription_id: int,
    subscription_data: SubscriptionUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update subscription (requires subscriptions:update permission)."""
    if not has_permission(current_user, "subscriptions:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    try:
        subscription = subscription_service.update_subscription(subscription_id, subscription_data)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/cancel", response_model=Subscription)
async def cancel_subscription(
    subscription_id: int,
    reason: Optional[str] = None,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel subscription (requires subscriptions:update permission)."""
    if not has_permission(current_user, "subscriptions:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    try:
        subscription = subscription_service.cancel_subscription(subscription_id, reason)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/renew", response_model=Subscription)
async def renew_subscription(
    subscription_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Renew subscription (requires subscriptions:update permission)."""
    if not has_permission(current_user, "subscriptions:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    try:
        subscription = subscription_service.renew_subscription(subscription_id)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/change-plan", response_model=Subscription)
async def change_subscription_plan(
    subscription_id: int,
    new_plan_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change subscription plan (requires subscriptions:update permission)."""
    if not has_permission(current_user, "subscriptions:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    subscription_service = SubscriptionService(db)
    try:
        subscription = subscription_service.change_plan(subscription_id, new_plan_id)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-expired")
async def check_expired_subscriptions(
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Check and update expired subscriptions (requires superuser)."""
    subscription_service = SubscriptionService(db)
    expired = subscription_service.check_expired_subscriptions()
    return {
        "message": f"Processed {len(expired)} expired subscriptions",
        "expired_count": len(expired)
    }


# Plan endpoints
@router.get("/plans/", response_model=List[Plan])
async def get_plans(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get plans (requires plans:read permission)."""
    if not has_permission(current_user, "plans:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    plan_service = PlanService(db)
    plans = plan_service.get_plans(skip=skip, limit=limit, is_active=is_active)
    return plans


@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get plan by ID (requires plans:read permission)."""
    if not has_permission(current_user, "plans:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    plan_service = PlanService(db)
    plan = plan_service.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/plans/", response_model=Plan, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new plan (requires plans:create permission)."""
    if not has_permission(current_user, "plans:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    plan_service = PlanService(db)
    try:
        plan = plan_service.create_plan(plan_data)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/plans/{plan_id}", response_model=Plan)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update plan (requires plans:update permission)."""
    if not has_permission(current_user, "plans:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    plan_service = PlanService(db)
    try:
        plan = plan_service.update_plan(plan_id, plan_data)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete plan (requires plans:delete permission)."""
    if not has_permission(current_user, "plans:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    plan_service = PlanService(db)
    try:
        plan_service.delete_plan(plan_id)
        return {"message": "Plan deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
