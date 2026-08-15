from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.schemas.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceFilter
from app.services.invoice import InvoiceService
from app.api.deps import get_current_user, get_client_ip, get_current_superuser
from app.models.user import User as UserModel
from app.core.rbac import has_permission

router = APIRouter()


@router.get("", response_model=List[Invoice])
async def get_invoices(
    search: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoices with filtering (requires invoices:read permission)."""
    if not has_permission(current_user, "invoices:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    filters = InvoiceFilter(
        search=search,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )
    invoices = invoice_service.get_invoices(filters)
    return invoices


@router.get("/statistics")
async def get_invoice_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice statistics (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    stats = invoice_service.get_invoice_statistics(date_from, date_to)
    return stats


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice by ID (requires invoices:read permission)."""
    if not has_permission(current_user, "invoices:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    invoice = invoice_service.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new invoice (requires invoices:create permission)."""
    if not has_permission(current_user, "invoices:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    try:
        invoice = invoice_service.create_invoice(invoice_data)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-order/{order_id}", response_model=Invoice)
async def create_invoice_from_order(
    order_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create invoice from order (requires invoices:create permission)."""
    if not has_permission(current_user, "invoices:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    try:
        invoice = invoice_service.create_invoice_from_order(order_id)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-subscription/{subscription_id}", response_model=Invoice)
async def create_invoice_from_subscription(
    subscription_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create invoice from subscription (requires invoices:create permission)."""
    if not has_permission(current_user, "invoices:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    try:
        invoice = invoice_service.create_invoice_from_subscription(subscription_id)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update invoice (requires invoices:update permission)."""
    if not has_permission(current_user, "invoices:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    try:
        invoice = invoice_service.update_invoice(invoice_id, invoice_data)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invoice_id}/mark-paid", response_model=Invoice)
async def mark_invoice_as_paid(
    invoice_id: int,
    payment_method: Optional[str] = None,
    transaction_id: Optional[str] = None,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark invoice as paid (requires invoices:update permission)."""
    if not has_permission(current_user, "invoices:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    try:
        invoice = invoice_service.mark_as_paid(invoice_id, payment_method, transaction_id)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mark-overdue")
async def mark_overdue_invoices(
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Mark overdue invoices (requires superuser)."""
    invoice_service = InvoiceService(db)
    overdue = invoice_service.mark_as_overdue()
    return {
        "message": f"Marked {len(overdue)} invoices as overdue",
        "overdue_count": len(overdue)
    }


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete invoice (requires invoices:delete permission)."""
    if not has_permission(current_user, "invoices:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invoice_service = InvoiceService(db)
    try:
        invoice_service.delete_invoice(invoice_id)
        return {"message": "Invoice deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
