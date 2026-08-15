from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.models.order import Order
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.user import User
from app.models.customer import Customer
from sqlalchemy import func, and_


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_financial_health(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get financial health metrics."""
        query = self.db.query(Order)
        
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        
        orders = query.all()
        
        # Revenue metrics
        total_revenue = sum(o.total_amount for o in orders if o.payment_status == "completed")
        pending_revenue = sum(o.total_amount for o in orders if o.payment_status == "pending")
        refunded_amount = sum(o.total_amount for o in orders if o.payment_status == "refunded")
        
        # Invoice metrics
        invoice_query = self.db.query(Invoice)
        if date_from:
            invoice_query = invoice_query.filter(Invoice.issue_date >= date_from)
        if date_to:
            invoice_query = invoice_query.filter(Invoice.issue_date <= date_to)
        
        invoices = invoice_query.all()
        accounts_receivable = sum(i.total_amount for i in invoices if i.status == "sent")
        
        # Subscription MRR
        sub_query = self.db.query(Subscription).filter(Subscription.status == "active")
        subscriptions = sub_query.all()
        mrr = sum(s.amount for s in subscriptions if s.plan.billing_cycle == "monthly")
        
        return {
            "total_revenue": total_revenue,
            "pending_revenue": pending_revenue,
            "refunded_amount": refunded_amount,
            "accounts_receivable": accounts_receivable,
            "monthly_recurring_revenue": mrr,
            "net_revenue": total_revenue - refunded_amount,
            "revenue_growth": self._calculate_revenue_growth(date_from, date_to)
        }

    def _calculate_revenue_growth(self, date_from: Optional[datetime], date_to: Optional[datetime]) -> float:
        """Calculate revenue growth percentage."""
        if not date_from or not date_to:
            return 0.0
        
        # Current period
        current_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(
                Order.created_at >= date_from,
                Order.created_at <= date_to,
                Order.payment_status == "completed"
            )
        ).scalar() or 0
        
        # Previous period (same duration)
        duration = date_to - date_from
        prev_date_from = date_from - duration
        prev_date_to = date_from
        
        prev_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(
                Order.created_at >= prev_date_from,
                Order.created_at <= prev_date_to,
                Order.payment_status == "completed"
            )
        ).scalar() or 0
        
        if prev_revenue == 0:
            return 100.0 if current_revenue > 0 else 0.0
        
        return ((current_revenue - prev_revenue) / prev_revenue) * 100

    def get_subscriber_retention(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get subscriber retention metrics."""
        query = self.db.query(Subscription)
        
        if date_from:
            query = query.filter(Subscription.created_at >= date_from)
        
        if date_to:
            query = query.filter(Subscription.created_at <= date_to)
        
        subscriptions = query.all()
        
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.status == "active"])
        cancelled_subscriptions = len([s for s in subscriptions if s.status == "cancelled"])
        trial_subscriptions = len([s for s in subscriptions if s.status == "trial"])
        
        # Calculate churn rate
        churn_rate = (cancelled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
        
        # Calculate retention rate
        retention_rate = ((active_subscriptions + trial_subscriptions) / total_subscriptions * 100) if total_subscriptions > 0 else 0
        
        # Average subscription lifetime
        cancelled_with_dates = [s for s in subscriptions if s.status == "cancelled" and s.cancelled_at and s.created_at]
        avg_lifetime_days = 0
        if cancelled_with_dates:
            lifetimes = [(s.cancelled_at - s.created_at).days for s in cancelled_with_dates]
            avg_lifetime_days = sum(lifetimes) / len(lifetimes)
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "cancelled_subscriptions": cancelled_subscriptions,
            "trial_subscriptions": trial_subscriptions,
            "churn_rate": churn_rate,
            "retention_rate": retention_rate,
            "average_lifetime_days": avg_lifetime_days
        }

    def get_customer_growth(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get customer growth metrics."""
        query = self.db.query(Customer)
        
        if date_from:
            query = query.filter(Customer.created_at >= date_from)
        
        if date_to:
            query = query.filter(Customer.created_at <= date_to)
        
        customers = query.all()
        
        total_customers = len(customers)
        
        # New customers by month
        customers_by_month = {}
        for customer in customers:
            month_key = customer.created_at.strftime("%Y-%m")
            customers_by_month[month_key] = customers_by_month.get(month_key, 0) + 1
        
        # Growth rate
        if len(customers_by_month) >= 2:
            months = sorted(customers_by_month.keys())
            current_month = months[-1]
            prev_month = months[-2]
            current_count = customers_by_month[current_month]
            prev_count = customers_by_month[prev_month]
            growth_rate = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
        else:
            growth_rate = 0
        
        return {
            "total_customers": total_customers,
            "customers_by_month": customers_by_month,
            "growth_rate": growth_rate,
            "average_daily_new_customers": total_customers / 30 if total_customers > 0 else 0
        }

    def get_revenue_by_period(self, period: str = "monthly", date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get revenue breakdown by time period."""
        query = self.db.query(
            func.date_trunc(period, Order.created_at).label("period"),
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("order_count")
        ).filter(Order.payment_status == "completed")
        
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        
        results = query.group_by(func.date_trunc(period, Order.created_at)).order_by(func.date_trunc(period, Order.created_at)).all()
        
        return [
            {
                "period": str(result.period),
                "revenue": float(result.revenue or 0),
                "order_count": result.order_count
            }
            for result in results
        ]

    def get_top_products(self, limit: int = 10, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get top selling products."""
        from app.models.order import OrderItem
        
        query = self.db.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.total_price).label("total_revenue")
        ).join(Order)
        
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        
        results = query.group_by(OrderItem.product_name).order_by(func.sum(OrderItem.total_price).desc()).limit(limit).all()
        
        return [
            {
                "product_name": result.product_name,
                "total_quantity": result.total_quantity,
                "total_revenue": float(result.total_revenue or 0)
            }
            for result in results
        ]

    def get_dashboard_summary(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get complete dashboard summary."""
        # Default to last 30 days if no dates provided
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        
        if not date_to:
            date_to = datetime.utcnow()
        
        return {
            "financial_health": self.get_financial_health(date_from, date_to),
            "subscriber_retention": self.get_subscriber_retention(date_from, date_to),
            "customer_growth": self.get_customer_growth(date_from, date_to),
            "revenue_by_month": self.get_revenue_by_period("monthly", date_from, date_to),
            "top_products": self.get_top_products(10, date_from, date_to),
            "period": {
                "from": str(date_from),
                "to": str(date_to)
            }
        }
