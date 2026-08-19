from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.subscription import Subscription, Plan
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionFilter, PlanCreate, PlanUpdate
from datetime import datetime, timedelta
import secrets
import json


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def generate_subscription_number(self) -> str:
        """Generate unique subscription number."""
        return f"SUB-{secrets.token_hex(4).upper()}"

    def get_subscriptions(self, filters: SubscriptionFilter) -> List[Subscription]:
        """Get subscriptions with filtering."""
        query = self.db.query(Subscription)
        
        # Search by subscription number
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                (Subscription.subscription_number.ilike(search_term))
            )
        
        # Status filter
        if filters.status:
            query = query.filter(Subscription.status == filters.status)
        
        # Customer filter
        if filters.customer_id:
            query = query.filter(Subscription.customer_id == filters.customer_id)
        
        # Plan filter
        if filters.plan_id:
            query = query.filter(Subscription.plan_id == filters.plan_id)
        
        # Date range filter
        if filters.date_from:
            query = query.filter(Subscription.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Subscription.created_at <= filters.date_to)
        
        return query.order_by(Subscription.created_at.desc()).offset(filters.skip).limit(filters.limit).all()

    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID."""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_subscription_by_number(self, subscription_number: str) -> Optional[Subscription]:
        """Get subscription by subscription number."""
        return self.db.query(Subscription).filter(Subscription.subscription_number == subscription_number).first()

    def get_subscription_by_gateway_id(self, gateway_id: str) -> Optional[Subscription]:
        """Get subscription by gateway subscription/payment ID."""
        return self.db.query(Subscription).filter(Subscription.gateway_subscription_id == gateway_id).first()

    def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Create a new subscription."""
        # Get plan
        plan = self.db.query(Plan).filter(Plan.id == subscription_data.plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        
        # Calculate dates based on plan
        now = datetime.utcnow()
        trial_start = None
        trial_end = None
        current_period_start = now
        current_period_end = None
        
        if plan.trial_days > 0:
            trial_start = now
            trial_end = now + timedelta(days=plan.trial_days)
            current_period_end = trial_end
        else:
            # Calculate period end based on billing cycle
            if plan.billing_cycle == "monthly":
                current_period_end = now + timedelta(days=30)
            elif plan.billing_cycle == "quarterly":
                current_period_end = now + timedelta(days=90)
            elif plan.billing_cycle == "yearly":
                current_period_end = now + timedelta(days=365)
        
        # Create subscription
        db_subscription = Subscription(
            subscription_number=self.generate_subscription_number(),
            customer_id=subscription_data.customer_id,
            plan_id=subscription_data.plan_id,
            status="trial" if plan.trial_days > 0 else "active",
            trial_start=trial_start,
            trial_end=trial_end,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            amount=subscription_data.amount,
            currency=subscription_data.currency,
            auto_renew=subscription_data.auto_renew,
            notes=subscription_data.notes,
        )
        
        self.db.add(db_subscription)
        self.db.commit()
        self.db.refresh(db_subscription)
        
        return db_subscription

    def update_subscription(self, subscription_id: int, subscription_data: SubscriptionUpdate) -> Subscription:
        """Update subscription."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        update_data = subscription_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(subscription, field, value)
        
        # Handle cancellation
        if subscription_data.status == "cancelled":
            subscription.cancelled_at = datetime.utcnow()
            subscription.expires_at = subscription.current_period_end
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def cancel_subscription(self, subscription_id: int, reason: Optional[str] = None) -> Subscription:
        """Cancel subscription."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        subscription.expires_at = subscription.current_period_end
        subscription.cancellation_reason = reason
        subscription.auto_renew = False
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def renew_subscription(self, subscription_id: int) -> Subscription:
        """Renew subscription."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        plan = subscription.plan
        now = datetime.utcnow()
        
        # Calculate new period end
        if plan.billing_cycle == "monthly":
            new_period_end = now + timedelta(days=30)
        elif plan.billing_cycle == "quarterly":
            new_period_end = now + timedelta(days=90)
        elif plan.billing_cycle == "yearly":
            new_period_end = now + timedelta(days=365)
        else:
            new_period_end = now + timedelta(days=30)
        
        subscription.current_period_start = now
        subscription.current_period_end = new_period_end
        subscription.status = "active"
        subscription.cancelled_at = None
        subscription.expires_at = None
        subscription.cancellation_reason = None
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def change_plan(self, subscription_id: int, new_plan_id: int) -> Subscription:
        """Change subscription plan."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        new_plan = self.db.query(Plan).filter(Plan.id == new_plan_id).first()
        if not new_plan:
            raise ValueError("New plan not found")
        
        subscription.plan_id = new_plan_id
        subscription.amount = new_plan.price
        
        # Recalculate period if needed
        now = datetime.utcnow()
        if new_plan.billing_cycle == "monthly":
            subscription.current_period_end = now + timedelta(days=30)
        elif new_plan.billing_cycle == "quarterly":
            subscription.current_period_end = now + timedelta(days=90)
        elif new_plan.billing_cycle == "yearly":
            subscription.current_period_end = now + timedelta(days=365)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def check_expired_subscriptions(self) -> List[Subscription]:
        """Check and update expired subscriptions."""
        now = datetime.utcnow()
        expired = self.db.query(Subscription).filter(
            Subscription.current_period_end < now,
            Subscription.status == "active"
        ).all()
        
        for subscription in expired:
            if subscription.auto_renew:
                # Auto-renew
                self.renew_subscription(subscription.id)
            else:
                # Mark as expired
                subscription.status = "expired"
                subscription.expires_at = now
        
        self.db.commit()
        
        return expired

    def get_subscription_statistics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> dict:
        """Get subscription statistics."""
        query = self.db.query(Subscription)
        
        if date_from:
            query = query.filter(Subscription.created_at >= date_from)
        
        if date_to:
            query = query.filter(Subscription.created_at <= date_to)
        
        subscriptions = query.all()
        
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.status == "active"])
        trial_subscriptions = len([s for s in subscriptions if s.status == "trial"])
        cancelled_subscriptions = len([s for s in subscriptions if s.status == "cancelled"])
        expired_subscriptions = len([s for s in subscriptions if s.status == "expired"])
        
        monthly_recurring_revenue = sum(
            s.amount for s in subscriptions 
            if s.status == "active" and s.plan.billing_cycle == "monthly"
        )
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "trial_subscriptions": trial_subscriptions,
            "cancelled_subscriptions": cancelled_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "monthly_recurring_revenue": monthly_recurring_revenue,
            "churn_rate": (cancelled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
        }


class PlanService:
    def __init__(self, db: Session):
        self.db = db

    def get_plans(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Plan]:
        """Get plans with optional filtering."""
        query = self.db.query(Plan)
        
        if is_active is not None:
            query = query.filter(Plan.is_active == is_active)
        
        return query.order_by(Plan.sort_order).offset(skip).limit(limit).all()

    def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """Get plan by ID."""
        return self.db.query(Plan).filter(Plan.id == plan_id).first()

    def get_plan_by_slug(self, slug: str) -> Optional[Plan]:
        """Get plan by slug."""
        return self.db.query(Plan).filter(Plan.slug == slug).first()

    def create_plan(self, plan_data: PlanCreate) -> Plan:
        """Create a new plan."""
        # Check if slug exists
        if self.get_plan_by_slug(plan_data.slug):
            raise ValueError("Plan slug already exists")
        
        db_plan = Plan(
            name=plan_data.name,
            slug=plan_data.slug,
            description=plan_data.description,
            price=plan_data.price,
            billing_cycle=plan_data.billing_cycle,
            trial_days=plan_data.trial_days,
            setup_fee=plan_data.setup_fee,
            max_users=plan_data.max_users,
            max_storage_gb=plan_data.max_storage_gb,
            features=plan_data.features,
            is_popular=plan_data.is_popular,
            is_active=plan_data.is_active,
            sort_order=plan_data.sort_order,
        )
        
        self.db.add(db_plan)
        self.db.commit()
        self.db.refresh(db_plan)
        
        return db_plan

    def update_plan(self, plan_id: int, plan_data: PlanUpdate) -> Plan:
        """Update plan."""
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        update_data = plan_data.model_dump(exclude_unset=True)
        
        # Check slug uniqueness if updating
        if "slug" in update_data:
            existing = self.get_plan_by_slug(update_data["slug"])
            if existing and existing.id != plan_id:
                raise ValueError("Plan slug already exists")
        
        for field, value in update_data.items():
            setattr(plan, field, value)
        
        self.db.commit()
        self.db.refresh(plan)
        
        return plan

    def delete_plan(self, plan_id: int) -> bool:
        """Delete plan."""
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        # Check if plan has active subscriptions
        active_subs = self.db.query(Subscription).filter(
            Subscription.plan_id == plan_id,
            Subscription.status == "active"
        ).first()
        
        if active_subs:
            raise ValueError("Cannot delete plan with active subscriptions")
        
        self.db.delete(plan)
        self.db.commit()
        
        return True
