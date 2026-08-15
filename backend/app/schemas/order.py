from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import enum


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethodEnum(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    RAZORPAY = "razorpay"
    GPAY = "gpay"
    BHIM = "bhim"
    BANK_TRANSFER = "bank_transfer"


class OrderItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    product_sku: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    product_snapshot: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_id: Optional[int] = None
    subtotal: float
    tax_amount: float = 0
    shipping_amount: float = 0
    discount_amount: float = 0
    total_amount: float
    currency: str = "USD"
    status: OrderStatusEnum = OrderStatusEnum.PENDING
    payment_status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    payment_method: Optional[PaymentMethodEnum] = None
    shipping_address: Optional[str] = None
    customer_notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: Optional[OrderStatusEnum] = None
    payment_status: Optional[PaymentStatusEnum] = None
    payment_method: Optional[PaymentMethodEnum] = None
    payment_gateway: Optional[str] = None
    payment_transaction_id: Optional[str] = None
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    admin_notes: Optional[str] = None


class Order(OrderBase):
    id: int
    order_number: str
    payment_gateway: Optional[str] = None
    payment_transaction_id: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItem] = []

    class Config:
        from_attributes = True


class OrderFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[OrderStatusEnum] = None
    payment_status: Optional[PaymentStatusEnum] = None
    customer_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
