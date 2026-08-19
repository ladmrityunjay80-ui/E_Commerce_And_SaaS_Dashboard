from pydantic import BaseModel
from typing import Optional


class PaymentCreateRequest(BaseModel):
    order_id: Optional[int] = None
    subscription_id: Optional[int] = None
    gateway: str  # stripe, razorpay, paypal
    payment_method: Optional[str] = None


class PaymentCreateResponse(BaseModel):
    gateway: str
    amount: float
    currency: str
    client_secret: Optional[str] = None
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    status: str
    message: str


class PaymentConfirmRequest(BaseModel):
    transaction_id: str
    gateway: str
    status: str


class PaymentWebhookPayload(BaseModel):
    payload: dict
    signature: Optional[str] = None
