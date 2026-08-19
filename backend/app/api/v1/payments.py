from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.payment import PaymentCreateRequest, PaymentCreateResponse, PaymentConfirmRequest
from app.services.payment import PaymentService
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User as UserModel
from app.core.rbac import has_permission

router = APIRouter()


@router.post("/create", response_model=PaymentCreateResponse)
async def create_payment(
    payment_data: PaymentCreateRequest,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent/order for an order or subscription."""
    if not has_permission(current_user, "orders:update"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = PaymentService(db)
    try:
        result = service.create_payment(
            order_id=payment_data.order_id,
            subscription_id=payment_data.subscription_id,
            gateway=payment_data.gateway,
            payment_method=payment_data.payment_method,
        )
        return PaymentCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhooks/{gateway}")
async def payment_webhook(
    gateway: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive payment gateway webhooks."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Stripe requires the raw body for signature verification
    if gateway == "stripe":
        raw_body = await request.body()
        payload["raw_body"] = raw_body.decode("utf-8")

    signature = request.headers.get("stripe-signature") or request.headers.get("x-razorpay-signature")

    service = PaymentService(db)
    try:
        result = service.process_webhook(gateway, payload, signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm")
async def confirm_payment(
    confirm_data: PaymentConfirmRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually confirm a payment (for testing or gateway redirects)."""
    if not has_permission(current_user, "orders:update"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = PaymentService(db)
    try:
        from app.services.order import OrderService
        order = OrderService(db).get_order_by_payment_transaction(confirm_data.transaction_id)
        if order:
            OrderService(db).update_payment_status(
                order.id,
                confirm_data.status,
                payment_gateway=confirm_data.gateway,
                transaction_id=confirm_data.transaction_id,
            )
            return {"status": "success", "message": f"Payment {confirm_data.transaction_id} confirmed"}

        # Try subscription
        from app.services.subscription import SubscriptionService
        subscription = SubscriptionService(db).get_subscription_by_gateway_id(confirm_data.transaction_id)
        if subscription:
            if confirm_data.status == "completed":
                subscription.status = "active"
            elif confirm_data.status == "failed":
                subscription.status = "past_due"
            subscription.payment_gateway = confirm_data.gateway
            db.commit()
            return {"status": "success", "message": f"Subscription payment {confirm_data.transaction_id} confirmed"}

        raise ValueError("Payment reference not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
