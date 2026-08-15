from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum


class InvoiceStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceBase(BaseModel):
    customer_id: Optional[int] = None
    order_id: Optional[int] = None
    subscription_id: Optional[int] = None
    subtotal: float
    tax_amount: float = 0
    discount_amount: float = 0
    total_amount: float
    currency: str = "USD"
    status: InvoiceStatusEnum = InvoiceStatusEnum.DRAFT
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    terms: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatusEnum] = None
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    payment_transaction_id: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None


class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    issue_date: datetime
    paid_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    payment_transaction_id: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[InvoiceStatusEnum] = None
    customer_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
