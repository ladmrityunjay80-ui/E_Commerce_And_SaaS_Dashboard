from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import enum


class SubscriptionStatusEnum(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycleEnum(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PlanBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    billing_cycle: BillingCycleEnum = BillingCycleEnum.MONTHLY
    trial_days: int = 0
    setup_fee: float = 0
    max_users: Optional[int] = None
    max_storage_gb: Optional[float] = None
    features: Optional[str] = None
    is_popular: bool = False
    is_active: bool = True
    sort_order: int = 0


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    billing_cycle: Optional[BillingCycleEnum] = None
    trial_days: Optional[int] = None
    setup_fee: Optional[float] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[float] = None
    features: Optional[str] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class Plan(PlanBase):
    id: int
    stripe_price_id: Optional[str] = None
    razorpay_plan_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    customer_id: Optional[int] = None
    plan_id: int
    amount: float
    currency: str = "USD"
    auto_renew: bool = True
    notes: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatusEnum] = None
    auto_renew: Optional[bool] = None
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None


class Subscription(SubscriptionBase):
    id: int
    subscription_number: str
    status: SubscriptionStatusEnum
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    payment_gateway: Optional[str] = None
    gateway_subscription_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    plan: Plan

    class Config:
        from_attributes = True


class SubscriptionFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[SubscriptionStatusEnum] = None
    customer_id: Optional[int] = None
    plan_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
