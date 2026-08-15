from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
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


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Pricing
    price = Column(Float, nullable=False)
    billing_cycle = Column(String(20), default=BillingCycleEnum.MONTHLY)
    trial_days = Column(Integer, default=0)
    setup_fee = Column(Float, default=0)
    
    # Limits
    max_users = Column(Integer, nullable=True)
    max_storage_gb = Column(Float, nullable=True)
    features = Column(Text, nullable=True)  # JSON array of features
    
    # Stripe/Payment gateway integration
    stripe_price_id = Column(String(255), nullable=True)
    razorpay_plan_id = Column(String(255), nullable=True)
    
    # Display
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    
    # Status
    status = Column(String(20), default=SubscriptionStatusEnum.TRIAL, index=True)
    
    # Dates
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Pricing
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment gateway
    payment_gateway = Column(String(50), nullable=True)
    gateway_subscription_id = Column(String(255), nullable=True)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    
    # Notes
    cancellation_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
