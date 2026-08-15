import pytest
from app.services.analytics import AnalyticsService
from app.models.order import Order, OrderItem
from app.models.subscription import Subscription
from app.models.customer import Customer
from datetime import datetime, timedelta


def test_get_financial_health(db_session):
    """Test financial health metrics calculation."""
    # Create test data
    customer = Customer(id=1, user_id=1)
    db_session.add(customer)
    
    order1 = Order(
        id=1,
        order_number="ORD-001",
        customer_id=1,
        subtotal=100,
        tax_amount=10,
        shipping_amount=5,
        discount_amount=0,
        total_amount=115,
        status="delivered",
        payment_status="completed",
        created_at=datetime.utcnow()
    )
    order2 = Order(
        id=2,
        order_number="ORD-002",
        customer_id=1,
        subtotal=50,
        tax_amount=5,
        shipping_amount=0,
        discount_amount=0,
        total_amount=55,
        status="pending",
        payment_status="pending",
        created_at=datetime.utcnow()
    )
    db_session.add_all([order1, order2])
    db_session.commit()
    
    analytics_service = AnalyticsService(db_session)
    metrics = analytics_service.get_financial_health()
    
    assert metrics["total_revenue"] == 115
    assert metrics["pending_revenue"] == 55
    assert metrics["net_revenue"] == 115


def test_get_subscriber_retention(db_session):
    """Test subscriber retention metrics calculation."""
    # Create test subscriptions
    from app.models.subscription import Plan
    
    plan = Plan(
        id=1,
        name="Pro Plan",
        slug="pro-plan",
        price=29.99,
        billing_cycle="monthly"
    )
    
    sub1 = Subscription(
        id=1,
        subscription_number="SUB-001",
        customer_id=1,
        plan_id=1,
        status="active",
        amount=29.99,
        created_at=datetime.utcnow()
    )
    sub2 = Subscription(
        id=2,
        subscription_number="SUB-002",
        customer_id=2,
        plan_id=1,
        status="cancelled",
        amount=29.99,
        cancelled_at=datetime.utcnow(),
        created_at=datetime.utcnow() - timedelta(days=30)
    )
    sub3 = Subscription(
        id=3,
        subscription_number="SUB-003",
        customer_id=3,
        plan_id=1,
        status="trial",
        amount=0,
        created_at=datetime.utcnow()
    )
    
    db_session.add_all([plan, sub1, sub2, sub3])
    db_session.commit()
    
    analytics_service = AnalyticsService(db_session)
    metrics = analytics_service.get_subscriber_retention()
    
    assert metrics["total_subscriptions"] == 3
    assert metrics["active_subscriptions"] == 1
    assert metrics["cancelled_subscriptions"] == 1
    assert metrics["trial_subscriptions"] == 1
    assert metrics["churn_rate"] == pytest.approx(33.33, rel=0.1)


def test_get_customer_growth(db_session):
    """Test customer growth metrics calculation."""
    # Create test customers
    customer1 = Customer(id=1, user_id=1, created_at=datetime.utcnow() - timedelta(days=10))
    customer2 = Customer(id=2, user_id=2, created_at=datetime.utcnow() - timedelta(days=5))
    customer3 = Customer(id=3, user_id=3, created_at=datetime.utcnow())
    
    db_session.add_all([customer1, customer2, customer3])
    db_session.commit()
    
    analytics_service = AnalyticsService(db_session)
    metrics = analytics_service.get_customer_growth()
    
    assert metrics["total_customers"] == 3
    assert "customers_by_month" in metrics


def test_get_top_products(db_session):
    """Test top products calculation."""
    from app.models.product import Product
    
    product = Product(
        id=1,
        name="Test Product",
        slug="test-product",
        price=10.00,
        stock_quantity=100
    )
    
    order = Order(
        id=1,
        order_number="ORD-001",
        customer_id=1,
        subtotal=20,
        tax_amount=0,
        shipping_amount=0,
        discount_amount=0,
        total_amount=20,
        status="delivered",
        payment_status="completed",
        created_at=datetime.utcnow()
    )
    
    order_item = OrderItem(
        id=1,
        order_id=1,
        product_id=1,
        product_name="Test Product",
        quantity=2,
        unit_price=10.00,
        total_price=20.00
    )
    
    db_session.add_all([product, order, order_item])
    db_session.commit()
    
    analytics_service = AnalyticsService(db_session)
    top_products = analytics_service.get_top_products(limit=10)
    
    assert len(top_products) == 1
    assert top_products[0]["product_name"] == "Test Product"
    assert top_products[0]["total_quantity"] == 2
    assert top_products[0]["total_revenue"] == 20.0
