from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.subscription import Subscription
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceFilter
from datetime import datetime, timedelta
import secrets


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        return f"INV-{secrets.token_hex(4).upper()}"

    def get_invoices(self, filters: InvoiceFilter) -> List[Invoice]:
        """Get invoices with filtering."""
        query = self.db.query(Invoice)
        
        # Search by invoice number
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                (Invoice.invoice_number.ilike(search_term))
            )
        
        # Status filter
        if filters.status:
            query = query.filter(Invoice.status == filters.status)
        
        # Customer filter
        if filters.customer_id:
            query = query.filter(Invoice.customer_id == filters.customer_id)
        
        # Date range filter
        if filters.date_from:
            query = query.filter(Invoice.issue_date >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Invoice.issue_date <= filters.date_to)
        
        return query.order_by(Invoice.issue_date.desc()).offset(filters.skip).limit(filters.limit).all()

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID."""
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return self.db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()

    def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice."""
        # Validate that at least one of order_id or subscription_id is provided
        if not invoice_data.order_id and not invoice_data.subscription_id:
            raise ValueError("Either order_id or subscription_id must be provided")
        
        # Validate order exists if provided
        if invoice_data.order_id:
            order = self.db.query(Order).filter(Order.id == invoice_data.order_id).first()
            if not order:
                raise ValueError("Order not found")
            # Auto-fill customer_id from order
            if not invoice_data.customer_id:
                invoice_data.customer_id = order.customer_id
        
        # Validate subscription exists if provided
        if invoice_data.subscription_id:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == invoice_data.subscription_id
            ).first()
            if not subscription:
                raise ValueError("Subscription not found")
            # Auto-fill customer_id from subscription
            if not invoice_data.customer_id:
                invoice_data.customer_id = subscription.customer_id
        
        # Calculate total
        total_amount = invoice_data.subtotal + invoice_data.tax_amount - invoice_data.discount_amount
        
        # Set default due date (30 days from issue date)
        if not invoice_data.due_date:
            invoice_data.due_date = datetime.utcnow() + timedelta(days=30)
        
        # Create invoice
        db_invoice = Invoice(
            invoice_number=self.generate_invoice_number(),
            customer_id=invoice_data.customer_id,
            order_id=invoice_data.order_id,
            subscription_id=invoice_data.subscription_id,
            subtotal=invoice_data.subtotal,
            tax_amount=invoice_data.tax_amount,
            discount_amount=invoice_data.discount_amount,
            total_amount=total_amount,
            currency=invoice_data.currency,
            status=invoice_data.status,
            due_date=invoice_data.due_date,
            notes=invoice_data.notes,
            terms=invoice_data.terms,
        )
        
        self.db.add(db_invoice)
        self.db.commit()
        self.db.refresh(db_invoice)
        
        return db_invoice

    def create_invoice_from_order(self, order_id: int) -> Invoice:
        """Create invoice from order."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        # Check if invoice already exists for this order
        existing = self.db.query(Invoice).filter(Invoice.order_id == order_id).first()
        if existing:
            raise ValueError("Invoice already exists for this order")
        
        invoice_data = InvoiceCreate(
            customer_id=order.customer_id,
            order_id=order_id,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            currency=order.currency,
            status="sent" if order.payment_status == "completed" else "draft",
            due_date=datetime.utcnow() + timedelta(days=30),
        )
        
        return self.create_invoice(invoice_data)

    def create_invoice_from_subscription(self, subscription_id: int) -> Invoice:
        """Create invoice from subscription."""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        if not subscription:
            raise ValueError("Subscription not found")
        
        invoice_data = InvoiceCreate(
            customer_id=subscription.customer_id,
            subscription_id=subscription_id,
            subtotal=subscription.amount,
            tax_amount=0,
            discount_amount=0,
            total_amount=subscription.amount,
            currency=subscription.currency,
            status="sent",
            due_date=datetime.utcnow() + timedelta(days=30),
        )
        
        return self.create_invoice(invoice_data)

    def update_invoice(self, invoice_id: int, invoice_data: InvoiceUpdate) -> Invoice:
        """Update invoice."""
        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        update_data = invoice_data.model_dump(exclude_unset=True)
        
        # Recalculate total if financial fields are updated
        if "subtotal" in update_data or "tax_amount" in update_data or "discount_amount" in update_data:
            subtotal = update_data.get("subtotal", invoice.subtotal)
            tax_amount = update_data.get("tax_amount", invoice.tax_amount)
            discount_amount = update_data.get("discount_amount", invoice.discount_amount)
            update_data["total_amount"] = subtotal + tax_amount - discount_amount
        
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        # Auto-update status based on paid_date
        if invoice_data.paid_date and not invoice.paid_date:
            invoice.status = "paid"
        
        self.db.commit()
        self.db.refresh(invoice)
        
        return invoice

    def mark_as_paid(self, invoice_id: int, payment_method: str = None, transaction_id: str = None) -> Invoice:
        """Mark invoice as paid."""
        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        invoice.status = "paid"
        invoice.paid_date = datetime.utcnow()
        
        if payment_method:
            invoice.payment_method = payment_method
        
        if transaction_id:
            invoice.payment_transaction_id = transaction_id
        
        self.db.commit()
        self.db.refresh(invoice)
        
        return invoice

    def mark_as_overdue(self) -> List[Invoice]:
        """Mark overdue invoices."""
        now = datetime.utcnow()
        overdue = self.db.query(Invoice).filter(
            Invoice.due_date < now,
            Invoice.status == "sent"
        ).all()
        
        for invoice in overdue:
            invoice.status = "overdue"
        
        self.db.commit()
        
        return overdue

    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete invoice."""
        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Only allow deletion of draft invoices
        if invoice.status != "draft":
            raise ValueError("Can only delete draft invoices")
        
        self.db.delete(invoice)
        self.db.commit()
        
        return True

    def get_invoice_statistics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> dict:
        """Get invoice statistics."""
        query = self.db.query(Invoice)
        
        if date_from:
            query = query.filter(Invoice.issue_date >= date_from)
        
        if date_to:
            query = query.filter(Invoice.issue_date <= date_to)
        
        invoices = query.all()
        
        total_invoices = len(invoices)
        total_amount = sum(invoice.total_amount for invoice in invoices)
        paid_amount = sum(invoice.total_amount for invoice in invoices if invoice.status == "paid")
        pending_amount = sum(invoice.total_amount for invoice in invoices if invoice.status == "sent")
        overdue_amount = sum(invoice.total_amount for invoice in invoices if invoice.status == "overdue")
        
        paid_invoices = len([i for i in invoices if i.status == "paid"])
        pending_invoices = len([i for i in invoices if i.status == "sent"])
        overdue_invoices = len([i for i in invoices if i.status == "overdue"])
        
        return {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "overdue_amount": overdue_amount,
            "paid_invoices": paid_invoices,
            "pending_invoices": pending_invoices,
            "overdue_invoices": overdue_invoices,
            "collection_rate": (paid_amount / total_amount * 100) if total_amount > 0 else 0
        }
