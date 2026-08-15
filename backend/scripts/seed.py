"""
Seed script for the SaaS Admin Dashboard with Indian sample data.
This script creates initial roles, admin user, and sample data for testing.
"""

import sys
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variable before importing
os.environ["DATABASE_URL"] = "sqlite:///saas_dashboard.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import hashlib
from app.models.user import User, Role
from app.models.customer import Customer
from app.models.product import Product, Category
from app.models.order import Order, OrderItem
from app.models.subscription import Subscription, Plan
from app.models.invoice import Invoice
from app.core.database import Base

# Simple password hash function for seeding
def simple_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Create simple SQLite engine
engine = create_engine("sqlite:///saas_dashboard.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Indian sample data
INDIAN_NAMES = [
    "Arjun Sharma", "Priya Patel", "Rahul Kumar", "Anita Singh", "Vikram Reddy",
    "Sneha Gupta", "Amit Verma", "Pooja Joshi", "Rajesh Mehta", "Kavita Nair",
    "Deepak Iyer", "Lakshmi Rao", "Sanjay Deshmukh", "Meena Sridhar", "Vikas Choudhury"
]

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Ahmedabad",
    "Jaipur", "Lucknow", "Kanpur", "Surat", "Nagpur", "Indore", "Bhopal", "Visakhapatnam"
]

INDIAN_STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana", "Gujarat", "Rajasthan",
    "Uttar Pradesh", "West Bengal", "Madhya Pradesh", "Kerala", "Punjab", "Haryana"
]

INDIAN_COMPANIES = [
    "Tata Consultancy Services", "Infosys Technologies", "Wipro Limited", "HCL Technologies",
    "Reliance Industries", "Mahindra & Mahindra", "Larsen & Toubro", "Adani Group",
    "Bharti Airtel", "State Bank of India", "ICICI Bank", "HDFC Bank"
]

INDIAN_INDUSTRIES = [
    "Information Technology", "Banking & Finance", "Manufacturing", "Telecommunications",
    "Healthcare", "E-commerce", "Education", "Real Estate", "Automotive", "Pharmaceuticals"
]

PRODUCT_NAMES = [
    "Premium Software License", "Cloud Storage Plan", "Enterprise CRM", "Project Management Tool",
    "Analytics Dashboard", "Communication Platform", "Security Suite", "Backup Solution",
    "API Access Package", "Developer Tools Bundle"
]

CATEGORY_NAMES = [
    "Software Licenses", "Cloud Services", "Business Tools", "Security", "Storage",
    "Communication", "Analytics", "Development Tools"
]

PLAN_NAMES = [
    "Starter Plan", "Professional Plan", "Enterprise Plan", "Business Plan", "Team Plan"
]


def create_roles(db: Session):
    """Create initial roles."""
    print("Creating roles...")
    
    roles_data = [
        {
            "name": "admin",
            "description": "Full system access with all permissions",
            "permissions": "users:read,users:create,users:update,users:delete,customers:read,customers:create,customers:update,customers:delete,products:read,products:create,products:update,products:delete,orders:read,orders:create,orders:update,orders:delete,subscriptions:read,subscriptions:create,subscriptions:update,subscriptions:delete,invoices:read,invoices:create,invoices:update,invoices:delete,plans:read,plans:create,plans:update,plans:delete,analytics:read,audit:read,impersonate:users,export:data"
        },
        {
            "name": "manager",
            "description": "Business operations and management access",
            "permissions": "customers:read,customers:create,customers:update,products:read,products:create,products:update,orders:read,orders:create,orders:update,subscriptions:read,subscriptions:create,subscriptions:update,invoices:read,invoices:create,plans:read,analytics:read,export:data"
        },
        {
            "name": "support",
            "description": "Customer support and view-only access",
            "permissions": "customers:read,products:read,orders:read,orders:update,subscriptions:read,invoices:read,analytics:read"
        },
        {
            "name": "customer",
            "description": "Regular customer with limited access",
            "permissions": "customers:read,products:read,orders:read,subscriptions:read,invoices:read"
        }
    ]
    
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            print(f"  Created role: {role_data['name']}")
        else:
            print(f"  Role already exists: {role_data['name']}")
    
    db.commit()


def create_admin_user(db: Session):
    """Create admin user with Indian sample data."""
    print("Creating admin user...")
    
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    
    existing_admin = db.query(User).filter(User.email == "admin@saasadmin.in").first()
    if existing_admin:
        print("  Admin user already exists")
        return existing_admin
    
    admin_user = User(
        email="admin@saasadmin.in",
        username="admin",
        full_name="Rajesh Kumar",
        phone="+91 98765 43210",
        hashed_password=simple_hash("Admin123"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    
    if admin_role:
        admin_user.roles.append(admin_role)
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"  Created admin user: {admin_user.email}")
    return admin_user


def create_sample_users(db: Session, count: int = 10):
    """Create sample users with Indian data."""
    print(f"Creating {count} sample users...")
    
    customer_role = db.query(Role).filter(Role.name == "customer").first()
    support_role = db.query(Role).filter(Role.name == "support").first()
    manager_role = db.query(Role).filter(Role.name == "manager").first()
    
    for i in range(count):
        name = INDIAN_NAMES[i % len(INDIAN_NAMES)]
        name_parts = name.split()
        username = f"{name_parts[0].lower()}{random.randint(100, 999)}"
        email = f"{username}@example.in"
        phone = f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"
        
        user = User(
            email=email,
            username=username,
            full_name=name,
            phone=phone,
            hashed_password=simple_hash("User123"),
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        
        # Assign roles based on index
        if i == 0:
            user.roles.append(manager_role)
        elif i == 1:
            user.roles.append(support_role)
        else:
            user.roles.append(customer_role)
        
        db.add(user)
        print(f"  Created user: {name} ({email})")
    
    db.commit()


def create_sample_customers(db: Session):
    """Create sample customers with Indian data."""
    print("Creating sample customers...")
    
    users = db.query(User).filter(User.email != "admin@saasadmin.in").all()
    
    for i, user in enumerate(users):
        existing_customer = db.query(Customer).filter(Customer.user_id == user.id).first()
        if existing_customer:
            continue
        
        customer = Customer(
            user_id=user.id,
            company_name=INDIAN_COMPANIES[i % len(INDIAN_COMPANIES)],
            industry=INDIAN_INDUSTRIES[i % len(INDIAN_INDUSTRIES)],
            address=f"{random.randint(1, 999)} {random.choice(['MG Road', 'Connaught Place', 'Anna Salai', 'Park Street'])}",
            city=INDIAN_CITIES[i % len(INDIAN_CITIES)],
            state=INDIAN_STATES[i % len(INDIAN_STATES)],
            country="India",
            postal_code=f"{random.randint(100000, 999999)}",
            tax_id=f"{random.randint(10, 99)}AAAC{random.randint(1000, 9999)}{random.choice(['A', 'B', 'C', 'D'])}",
        )
        
        db.add(customer)
        print(f"  Created customer: {customer.company_name}")
    
    db.commit()


def create_sample_categories(db: Session):
    """Create sample product categories."""
    print("Creating sample categories...")
    
    for category_name in CATEGORY_NAMES:
        existing = db.query(Category).filter(Category.name == category_name).first()
        if existing:
            continue
        
        slug = category_name.lower().replace(" ", "-").replace("&", "and")
        category = Category(
            name=category_name,
            slug=slug,
            description=f"{category_name} for your business needs",
            is_active=True,
        )
        
        db.add(category)
        print(f"  Created category: {category_name}")
    
    db.commit()


def create_sample_products(db: Session, count: int = 15):
    """Create sample products with Indian pricing."""
    print(f"Creating {count} sample products...")
    
    categories = db.query(Category).all()
    
    for i in range(count):
        product_name = PRODUCT_NAMES[i % len(PRODUCT_NAMES)]
        slug = f"{product_name.lower().replace(' ', '-').replace('/', '-')}-{i}"
        sku = f"IND-{random.randint(10000, 99999)}"
        
        # Indian pricing in INR
        base_price = random.randint(999, 49999)
        
        product = Product(
            name=product_name,
            slug=slug,
            description=f"Premium {product_name} designed for Indian businesses. Includes 24/7 support and GST compliance.",
            sku=sku,
            price=base_price,
            compare_price=base_price + random.randint(1000, 5000),
            stock_quantity=random.randint(10, 100),
            low_stock_threshold=15,
            status=random.choice(["active", "active", "active", "draft"]),
            is_featured=random.choice([True, False]),
            is_digital=random.choice([True, False]),
            meta_title=f"{product_name} - Best Price in India",
            meta_description=f"Buy {product_name} at best price in India. GST included with invoice.",
        )
        
        # Assign random categories
        num_categories = random.randint(1, 2)
        selected_categories = random.sample(categories, min(num_categories, len(categories)))
        product.categories.extend(selected_categories)
        
        db.add(product)
        print(f"  Created product: {product_name} (₹{base_price})")
    
    db.commit()


def create_sample_plans(db: Session):
    """Create sample subscription plans with Indian pricing."""
    print("Creating sample subscription plans...")
    
    plans_data = [
        {
            "name": "Starter Plan",
            "slug": "starter-plan",
            "description": "Perfect for small businesses and startups in India",
            "price": 999,
            "billing_cycle": "monthly",
            "trial_days": 14,
            "setup_fee": 0,
            "max_users": 5,
            "max_storage_gb": 10,
            "features": '["Basic Analytics", "Email Support", "5GB Storage", "5 User Accounts"]',
            "is_popular": False,
            "sort_order": 1
        },
        {
            "name": "Professional Plan",
            "slug": "professional-plan",
            "description": "Ideal for growing businesses with advanced features",
            "price": 2499,
            "billing_cycle": "monthly",
            "trial_days": 7,
            "setup_fee": 0,
            "max_users": 25,
            "max_storage_gb": 50,
            "features": '["Advanced Analytics", "Priority Support", "50GB Storage", "25 User Accounts", "API Access"]',
            "is_popular": True,
            "sort_order": 2
        },
        {
            "name": "Enterprise Plan",
            "slug": "enterprise-plan",
            "description": "Comprehensive solution for large enterprises",
            "price": 9999,
            "billing_cycle": "monthly",
            "trial_days": 0,
            "setup_fee": 5000,
            "max_users": 100,
            "max_storage_gb": 500,
            "features": '["Custom Analytics", "24/7 Phone Support", "500GB Storage", "100 User Accounts", "API Access", "Custom Integrations", "Dedicated Account Manager"]',
            "is_popular": False,
            "sort_order": 3
        }
    ]
    
    for plan_data in plans_data:
        existing = db.query(Plan).filter(Plan.slug == plan_data["slug"]).first()
        if existing:
            continue
        
        plan = Plan(**plan_data)
        db.add(plan)
        print(f"  Created plan: {plan_data['name']} (₹{plan_data['price']}/month)")
    
    db.commit()


def create_sample_orders(db: Session, count: int = 20):
    """Create sample orders with Indian context."""
    print(f"Creating {count} sample orders...")
    
    customers = db.query(Customer).all()
    products = db.query(Product).filter(Product.status == "active").all()
    
    for i in range(count):
        customer = random.choice(customers)
        
        # Generate order number
        order_number = f"ORD-{random.randint(10000, 99999)}"
        
        # Random number of items (1-3)
        num_items = random.randint(1, 3)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        subtotal = sum(p.price * random.randint(1, 3) for p in selected_products)
        tax_amount = subtotal * 0.18  # 18% GST
        shipping_amount = random.choice([0, 99, 199, 299])
        discount_amount = random.choice([0, subtotal * 0.1])
        total_amount = subtotal + tax_amount + shipping_amount - discount_amount
        
        order = Order(
            order_number=order_number,
            customer_id=customer.id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency="INR",
            status=random.choice(["pending", "processing", "shipped", "delivered", "delivered"]),
            payment_status=random.choice(["completed", "completed", "completed", "pending"]),
            payment_method=random.choice(["credit_card", "razorpay", "gpay", "bhim"]),
            shipping_address=f"{customer.address}, {customer.city}, {customer.state} - {customer.postal_code}",
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
        )
        
        db.add(order)
        db.flush()
        
        # Create order items
        for product in selected_products:
            quantity = random.randint(1, 3)
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=quantity,
                unit_price=product.price,
                total_price=product.price * quantity,
                product_snapshot=f'{{"name": "{product.name}", "price": {product.price}, "sku": "{product.sku}"}}'
            )
            db.add(order_item)
        
        print(f"  Created order: {order_number} (₹{total_amount:.2f})")
    
    db.commit()


def create_sample_subscriptions(db: Session, count: int = 10):
    """Create sample subscriptions."""
    print(f"Creating {count} sample subscriptions...")
    
    customers = db.query(Customer).all()
    plans = db.query(Plan).all()
    
    for i in range(count):
        customer = random.choice(customers)
        plan = random.choice(plans)
        
        subscription_number = f"SUB-{random.randint(10000, 99999)}"
        
        # Calculate dates
        now = datetime.utcnow()
        trial_start = now if plan.trial_days > 0 else None
        trial_end = now + timedelta(days=plan.trial_days) if plan.trial_days > 0 else None
        current_period_start = now
        current_period_end = now + timedelta(days=30) if plan.billing_cycle == "monthly" else now + timedelta(days=365)
        
        subscription = Subscription(
            subscription_number=subscription_number,
            customer_id=customer.id,
            plan_id=plan.id,
            status="trial" if plan.trial_days > 0 else "active",
            trial_start=trial_start,
            trial_end=trial_end,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            amount=plan.price,
            currency="INR",
            auto_renew=random.choice([True, True, False]),
            created_at=now - timedelta(days=random.randint(1, 60)),
        )
        
        db.add(subscription)
        print(f"  Created subscription: {subscription_number} ({plan.name})")
    
    db.commit()


def create_sample_invoices(db: Session, count: int = 15):
    """Create sample invoices with GST."""
    print(f"Creating {count} sample invoices...")
    
    customers = db.query(Customer).all()
    orders = db.query(Order).filter(Order.payment_status == "completed").all()
    
    for i in range(count):
        customer = random.choice(customers)
        
        # Some invoices from orders, some standalone
        if orders and random.choice([True, False]):
            order = random.choice(orders)
            subtotal = order.subtotal
            tax_amount = order.tax_amount
            discount_amount = order.discount_amount
            total_amount = order.total_amount
            order_id = order.id
            subscription_id = None
        else:
            subtotal = random.randint(1000, 50000)
            tax_amount = subtotal * 0.18  # 18% GST
            discount_amount = 0
            total_amount = subtotal + tax_amount
            order_id = None
            subscription_id = None
        
        invoice_number = f"INV-{random.randint(10000, 99999)}"
        
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=customer.id,
            order_id=order_id,
            subscription_id=subscription_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency="INR",
            status=random.choice(["paid", "paid", "paid", "sent", "overdue"]),
            issue_date=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            due_date=datetime.utcnow() + timedelta(days=30),
            notes="GST included as per Indian tax laws",
        )
        
        db.add(invoice)
        print(f"  Created invoice: {invoice_number} (₹{total_amount:.2f})")
    
    db.commit()


def seed_database():
    """Main function to seed the database with Indian sample data."""
    print("Starting database seeding with Indian sample data...")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create roles
        create_roles(db)
        
        # Create admin user
        create_admin_user(db)
        
        # Create sample users
        create_sample_users(db, count=10)
        
        # Create sample customers
        create_sample_customers(db)
        
        # Create sample categories
        create_sample_categories(db)
        
        # Create sample products
        create_sample_products(db, count=15)
        
        # Create sample plans
        create_sample_plans(db)
        
        # Create sample orders
        create_sample_orders(db, count=20)
        
        # Create sample subscriptions
        create_sample_subscriptions(db, count=10)
        
        # Create sample invoices
        create_sample_invoices(db, count=15)
        
        print("=" * 60)
        print("Database seeding completed successfully!")
        print("\nSample data created:")
        print("  - 4 Roles (admin, manager, support, customer)")
        print("  - 1 Admin user (admin@saasadmin.in / Admin@123)")
        print("  - 10 Sample users with Indian names and data")
        print("  - 10 Sample customers with Indian companies")
        print("  - 8 Product categories")
        print("  - 15 Sample products with INR pricing")
        print("  - 3 Subscription plans with Indian pricing")
        print("  - 20 Sample orders with GST")
        print("  - 10 Sample subscriptions")
        print("  - 15 Sample invoices with GST")
        print("\nDefault login credentials:")
        print("  Email: admin@saasadmin.in")
        print("  Password: Admin@123")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
