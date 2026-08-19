from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, OrderFilter
from datetime import datetime
import secrets
import json


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def generate_order_number(self) -> str:
        """Generate unique order number."""
        return f"ORD-{secrets.token_hex(4).upper()}"

    def get_orders(self, filters: OrderFilter) -> List[Order]:
        """Get orders with filtering."""
        query = self.db.query(Order)
        
        # Search by order number or customer email
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                (Order.order_number.ilike(search_term))
            )
        
        # Status filter
        if filters.status:
            query = query.filter(Order.status == filters.status)
        
        # Payment status filter
        if filters.payment_status:
            query = query.filter(Order.payment_status == filters.payment_status)
        
        # Customer filter
        if filters.customer_id:
            query = query.filter(Order.customer_id == filters.customer_id)
        
        # Date range filter
        if filters.date_from:
            query = query.filter(Order.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Order.created_at <= filters.date_to)
        
        return query.order_by(Order.created_at.desc()).offset(filters.skip).limit(filters.limit).all()

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_order_by_payment_transaction(self, transaction_id: str) -> Optional[Order]:
        """Get order by payment transaction ID."""
        return self.db.query(Order).filter(Order.payment_transaction_id == transaction_id).first()

    def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        return self.db.query(Order).filter(Order.order_number == order_number).first()

    def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order."""
        # Validate and calculate totals
        subtotal = 0
        order_items = []
        
        for item_data in order_data.items:
            # Get product for validation
            product = self.db.query(Product).filter(Product.id == item_data.product_id).first()
            if not product:
                raise ValueError(f"Product with ID {item_data.product_id} not found")
            
            # Check stock
            if product.stock_quantity < item_data.quantity:
                raise ValueError(f"Insufficient stock for product {product.name}")
            
            # Calculate item total
            item_total = item_data.quantity * item_data.unit_price
            subtotal += item_total
            
            # Create order item
            order_item = OrderItem(
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                product_sku=item_data.product_sku,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=item_total,
                product_snapshot=json.dumps({
                    "name": product.name,
                    "sku": product.sku,
                    "price": product.price,
                    "image_url": product.image_url
                })
            )
            order_items.append(order_item)
            
            # Update stock
            product.stock_quantity -= item_data.quantity
        
        # Calculate order total
        total_amount = subtotal + order_data.tax_amount + order_data.shipping_amount - order_data.discount_amount
        
        # Create order
        db_order = Order(
            order_number=self.generate_order_number(),
            customer_id=order_data.customer_id,
            subtotal=subtotal,
            tax_amount=order_data.tax_amount,
            shipping_amount=order_data.shipping_amount,
            discount_amount=order_data.discount_amount,
            total_amount=total_amount,
            currency=order_data.currency,
            status=order_data.status,
            payment_status=order_data.payment_status,
            payment_method=order_data.payment_method,
            shipping_address=order_data.shipping_address,
            customer_notes=order_data.customer_notes,
        )
        
        self.db.add(db_order)
        self.db.flush()  # Get order ID before adding items
        
        # Add items to order
        for item in order_items:
            item.order_id = db_order.id
            self.db.add(item)
        
        self.db.commit()
        self.db.refresh(db_order)
        
        return db_order

    def update_order(self, order_id: int, order_data: OrderUpdate) -> Order:
        """Update order."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        update_data = order_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(order, field, value)
        
        self.db.commit()
        self.db.refresh(order)
        
        return order

    def update_order_status(self, order_id: int, status: str) -> Order:
        """Update order status."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        order.status = status
        
        # Auto-update payment status based on order status
        if status == "cancelled":
            order.payment_status = "refunded"
            # Restore stock
            for item in order.items:
                if item.product:
                    item.product.stock_quantity += item.quantity
        elif status == "delivered":
            order.actual_delivery = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(order)
        
        return order

    def update_payment_status(self, order_id: int, payment_status: str, payment_gateway: str = None, transaction_id: str = None) -> Order:
        """Update payment status."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        order.payment_status = payment_status
        
        if payment_gateway:
            order.payment_gateway = payment_gateway
        
        if transaction_id:
            order.payment_transaction_id = transaction_id
        
        # Update order status based on payment
        if payment_status == "completed":
            order.status = "processing"
        elif payment_status == "failed":
            order.status = "cancelled"
        
        self.db.commit()
        self.db.refresh(order)
        
        return order

    def delete_order(self, order_id: int) -> bool:
        """Delete order."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        # Restore stock before deleting
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity
        
        self.db.delete(order)
        self.db.commit()
        
        return True

    def get_order_statistics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> dict:
        """Get order statistics."""
        query = self.db.query(Order)
        
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        
        orders = query.all()
        
        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders if order.payment_status == "completed")
        pending_orders = len([o for o in orders if o.status == "pending"])
        completed_orders = len([o for o in orders if o.status == "delivered"])
        cancelled_orders = len([o for o in orders if o.status == "cancelled"])
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "average_order_value": total_revenue / completed_orders if completed_orders > 0 else 0
        }
