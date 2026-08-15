from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.schemas.order import Order, OrderCreate, OrderUpdate, OrderFilter
from app.services.order import OrderService
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User as UserModel
from app.core.rbac import has_permission
from app.models.audit import AuditActionEnum

router = APIRouter()


@router.get("", response_model=List[Order])
async def get_orders(
    search: Optional[str] = None,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get orders with filtering (requires orders:read permission)."""
    if not has_permission(current_user, "orders:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    filters = OrderFilter(
        search=search,
        status=status,
        payment_status=payment_status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )
    orders = order_service.get_orders(filters)
    return orders


@router.get("/statistics")
async def get_order_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order statistics (requires analytics:read permission)."""
    if not has_permission(current_user, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    stats = order_service.get_order_statistics(date_from, date_to)
    return stats


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order by ID (requires orders:read permission)."""
    if not has_permission(current_user, "orders:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order (requires orders:create permission)."""
    if not has_permission(current_user, "orders:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    try:
        order = order_service.create_order(order_data)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}", response_model=Order)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order (requires orders:update permission)."""
    if not has_permission(current_user, "orders:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    try:
        order = order_service.update_order(order_id, order_data)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: int,
    status: str,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order status (requires orders:update permission)."""
    if not has_permission(current_user, "orders:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    try:
        order = order_service.update_order_status(order_id, status)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/payment-status", response_model=Order)
async def update_payment_status(
    order_id: int,
    payment_status: str,
    payment_gateway: Optional[str] = None,
    transaction_id: Optional[str] = None,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update payment status (requires orders:update permission)."""
    if not has_permission(current_user, "orders:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    try:
        order = order_service.update_payment_status(order_id, payment_status, payment_gateway, transaction_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete order (requires orders:delete permission)."""
    if not has_permission(current_user, "orders:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    order_service = OrderService(db)
    try:
        order_service.delete_order(order_id)
        return {"message": "Order deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
