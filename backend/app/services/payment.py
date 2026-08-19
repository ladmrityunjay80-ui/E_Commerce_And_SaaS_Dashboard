from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.order import Order
from app.models.subscription import Subscription
from app.services.order import OrderService
from app.services.subscription import SubscriptionService


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def _get_order_or_subscription(self, order_id: Optional[int], subscription_id: Optional[int]):
        if order_id:
            order = OrderService(self.db).get_order_by_id(order_id)
            if not order:
                raise ValueError("Order not found")
            return order, None

        if subscription_id:
            subscription = SubscriptionService(self.db).get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError("Subscription not found")
            return None, subscription

        raise ValueError("Either order_id or subscription_id is required")

    def create_payment(self, order_id: Optional[int], subscription_id: Optional[int], gateway: str, payment_method: Optional[str]) -> Dict[str, Any]:
        order, subscription = self._get_order_or_subscription(order_id, subscription_id)

        if gateway == "stripe":
            return self._create_stripe_payment(order, subscription, payment_method)
        elif gateway == "razorpay":
            return self._create_razorpay_payment(order, subscription, payment_method)
        elif gateway == "paypal":
            return self._create_paypal_payment(order, subscription, payment_method)
        else:
            raise ValueError(f"Unsupported payment gateway: {gateway}")

    def _create_stripe_payment(self, order: Optional[Order], subscription: Optional[Subscription], payment_method: Optional[str]) -> Dict[str, Any]:
        if not settings.STRIPE_API_KEY:
            return self._mock_response(order, subscription, "stripe", "Stripe API key not configured")

        import stripe as stripe_lib
        stripe_lib.api_key = settings.STRIPE_API_KEY

        amount, currency, metadata = self._payment_context(order, subscription)

        try:
            intent = stripe_lib.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                metadata=metadata,
                payment_method_types=["card"],
            )
            self._record_gateway(order, subscription, "stripe", intent.id)
            return {
                "gateway": "stripe",
                "amount": amount,
                "currency": currency,
                "client_secret": intent.client_secret,
                "gateway_payment_id": intent.id,
                "status": "pending",
                "message": "Payment intent created",
            }
        except Exception as e:
            return self._mock_response(order, subscription, "stripe", f"Stripe error: {str(e)}")

    def _create_razorpay_payment(self, order: Optional[Order], subscription: Optional[Subscription], payment_method: Optional[str]) -> Dict[str, Any]:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return self._mock_response(order, subscription, "razorpay", "Razorpay keys not configured")

        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        amount, currency, notes = self._payment_context(order, subscription)

        try:
            rz_order = client.order.create({
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": f"rcpt_{(order.id if order else subscription.id)}",
                "notes": notes,
            })
            self._record_gateway(order, subscription, "razorpay", rz_order["id"])
            return {
                "gateway": "razorpay",
                "amount": amount,
                "currency": currency,
                "gateway_order_id": rz_order["id"],
                "status": "pending",
                "message": "Razorpay order created",
            }
        except Exception as e:
            return self._mock_response(order, subscription, "razorpay", f"Razorpay error: {str(e)}")

    def _create_paypal_payment(self, order: Optional[Order], subscription: Optional[Subscription], payment_method: Optional[str]) -> Dict[str, Any]:
        if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
            return self._mock_response(order, subscription, "paypal", "PayPal credentials not configured")

        import paypalrestsdk
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })

        amount, currency, _ = self._payment_context(order, subscription)

        try:
            paypal_payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": payment_method or "paypal"},
                "transactions": [{
                    "amount": {"total": f"{amount:.2f}", "currency": currency},
                    "description": f"Payment for order/subscription {(order.id if order else subscription.id)}",
                }],
                "redirect_urls": {
                    "return_url": f"{settings.FRONTEND_URL}/payments/success",
                    "cancel_url": f"{settings.FRONTEND_URL}/payments/cancel",
                },
            })
            if paypal_payment.create():
                self._record_gateway(order, subscription, "paypal", paypal_payment.id)
                return {
                    "gateway": "paypal",
                    "amount": amount,
                    "currency": currency,
                    "gateway_payment_id": paypal_payment.id,
                    "status": "pending",
                    "message": "PayPal payment created",
                }
            else:
                return self._mock_response(order, subscription, "paypal", f"PayPal error: {paypal_payment.error}")
        except Exception as e:
            return self._mock_response(order, subscription, "paypal", f"PayPal error: {str(e)}")

    def _payment_context(self, order: Optional[Order], subscription: Optional[Subscription]):
        if order:
            return (
                order.total_amount,
                order.currency or "USD",
                {
                    "order_id": str(order.id),
                    "type": "order",
                    "payment_method": order.payment_method or "card",
                },
            )

        if subscription:
            return (
                subscription.amount,
                subscription.currency or "USD",
                {
                    "subscription_id": str(subscription.id),
                    "type": "subscription",
                    "payment_method": "card",
                },
            )

    def _record_gateway(self, order: Optional[Order], subscription: Optional[Subscription], gateway: str, transaction_id: str):
        if order:
            order.payment_gateway = gateway
            order.payment_transaction_id = transaction_id
            self.db.commit()
        elif subscription:
            subscription.payment_gateway = gateway
            subscription.gateway_subscription_id = transaction_id
            self.db.commit()

    def _mock_response(self, order: Optional[Order], subscription: Optional[Subscription], gateway: str, message: str) -> Dict[str, Any]:
        amount, currency, _ = self._payment_context(order, subscription)
        return {
            "gateway": gateway,
            "amount": amount,
            "currency": currency,
            "client_secret": None,
            "gateway_order_id": None,
            "gateway_payment_id": None,
            "status": "not_configured",
            "message": message,
        }

    def process_webhook(self, gateway: str, payload: Dict[str, Any], signature: Optional[str]) -> Dict[str, Any]:
        if gateway == "stripe":
            return self._process_stripe_webhook(payload, signature)
        elif gateway == "razorpay":
            return self._process_razorpay_webhook(payload, signature)
        elif gateway == "paypal":
            return self._process_paypal_webhook(payload)
        else:
            raise ValueError(f"Unsupported payment gateway: {gateway}")

    def _process_stripe_webhook(self, payload: Dict[str, Any], signature: Optional[str]) -> Dict[str, Any]:
        import stripe as stripe_lib

        if not settings.STRIPE_WEBHOOK_SECRET:
            event = payload
        else:
            try:
                event = stripe_lib.Webhook.construct_event(
                    payload.get("raw_body", ""),
                    signature or "",
                    settings.STRIPE_WEBHOOK_SECRET,
                )
            except Exception as e:
                return {"status": "error", "message": f"Invalid Stripe webhook signature: {str(e)}"}

        event_type = event.get("type")
        intent = event.get("data", {}).get("object", {})
        metadata = intent.get("metadata", {})

        if event_type == "payment_intent.succeeded":
            self._mark_paid(metadata, "completed", intent.get("id"))
            return {"status": "success", "message": "Payment marked as completed"}
        elif event_type == "payment_intent.payment_failed":
            self._mark_paid(metadata, "failed", intent.get("id"))
            return {"status": "success", "message": "Payment marked as failed"}

        return {"status": "ignored", "message": f"Unhandled event type: {event_type}"}

    def _process_razorpay_webhook(self, payload: Dict[str, Any], signature: Optional[str]) -> Dict[str, Any]:
        if not settings.RAZORPAY_KEY_SECRET:
            pass
        else:
            try:
                import razorpay
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID or "", settings.RAZORPAY_KEY_SECRET))
                client.utility.verify_webhook_signature(
                    str(payload),
                    signature or "",
                    settings.RAZORPAY_KEY_SECRET,
                )
            except Exception as e:
                return {"status": "error", "message": f"Invalid Razorpay signature: {str(e)}"}

        event = payload.get("event")
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment.get("notes", {})

        if event == "payment.captured":
            self._mark_paid(notes, "completed", payment.get("id"))
            return {"status": "success", "message": "Payment marked as completed"}
        elif event == "payment.failed":
            self._mark_paid(notes, "failed", payment.get("id"))
            return {"status": "success", "message": "Payment marked as failed"}

        return {"status": "ignored", "message": f"Unhandled event: {event}"}

    def _process_paypal_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type = payload.get("event_type")
        resource = payload.get("resource", {})
        invoice_number = resource.get("invoice_number") or resource.get("id")

        if event_type == "PAYMENT.SALE.COMPLETED":
            return {"status": "success", "message": f"PayPal payment {invoice_number} completed"}
        elif event_type == "PAYMENT.SALE.DENIED":
            return {"status": "success", "message": f"PayPal payment {invoice_number} denied"}

        return {"status": "ignored", "message": f"Unhandled PayPal event: {event_type}"}

    def _mark_paid(self, metadata: Dict[str, Any], payment_status: str, transaction_id: str):
        order_id = metadata.get("order_id")
        subscription_id = metadata.get("subscription_id")

        if order_id:
            order = OrderService(self.db).get_order_by_id(int(order_id))
            if order:
                OrderService(self.db).update_payment_status(
                    order.id,
                    payment_status,
                    payment_gateway=order.payment_gateway,
                    transaction_id=transaction_id,
                )

        if subscription_id:
            subscription = SubscriptionService(self.db).get_subscription_by_id(int(subscription_id))
            if subscription:
                if payment_status == "completed":
                    subscription.status = "active"
                    if subscription.current_period_end:
                        subscription.current_period_start = datetime.utcnow()
                        subscription.current_period_end = subscription.current_period_end + timedelta(days=30)
                elif payment_status == "failed":
                    subscription.status = "past_due"
                subscription.payment_gateway = subscription.payment_gateway or metadata.get("gateway")
                self.db.commit()
