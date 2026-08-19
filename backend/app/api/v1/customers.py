from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.customer import Customer, CustomerCreate, CustomerUpdate
from app.services.customer import CustomerService
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User as UserModel
from app.core.rbac import has_permission
from app.models.audit import AuditActionEnum

router = APIRouter()


@router.get("", response_model=List[Customer])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customers (requires customers:read permission)."""
    if not has_permission(current_user, "customers:read"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = CustomerService(db)
    return service.get_customers(skip=skip, limit=limit, search=search)


@router.get("/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer by ID (requires customers:read permission)."""
    if not has_permission(current_user, "customers:read"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = CustomerService(db)
    customer = service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a customer (requires customers:create permission)."""
    if not has_permission(current_user, "customers:create"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = CustomerService(db)
    try:
        customer = service.create_customer(customer_data)
        return customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer (requires customers:update permission)."""
    if not has_permission(current_user, "customers:update"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = CustomerService(db)
    try:
        customer = service.update_customer(customer_id, customer_data)
        return customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete customer (requires customers:delete permission)."""
    if not has_permission(current_user, "customers:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = CustomerService(db)
    try:
        service.delete_customer(customer_id)
        return {"message": "Customer deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
