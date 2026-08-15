from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductFilter, Category, CategoryCreate, CategoryUpdate
from app.services.product import ProductService, CategoryService
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User as UserModel
from app.core.rbac import has_permission
from app.models.audit import AuditActionEnum

router = APIRouter()


# Product endpoints
@router.get("", response_model=List[Product])
async def get_products(
    search: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    is_featured: Optional[bool] = None,
    is_digital: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get products with filtering (requires products:read permission)."""
    if not has_permission(current_user, "products:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    filters = ProductFilter(
        search=search,
        status=status,
        category_id=category_id,
        is_featured=is_featured,
        is_digital=is_digital,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        skip=skip,
        limit=limit
    )
    products = product_service.get_products(filters)
    return products


@router.get("/low-stock", response_model=List[Product])
async def get_low_stock_products(
    threshold: Optional[int] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get products with low stock (requires products:read permission)."""
    if not has_permission(current_user, "products:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    products = product_service.get_low_stock_products(threshold)
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product by ID (requires products:read permission)."""
    if not has_permission(current_user, "products:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product (requires products:create permission)."""
    if not has_permission(current_user, "products:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    try:
        product = product_service.create_product(product_data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update product (requires products:update permission)."""
    if not has_permission(current_user, "products:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    try:
        product = product_service.update_product(product_id, product_data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete product (requires products:delete permission)."""
    if not has_permission(current_user, "products:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    try:
        product_service.delete_product(product_id)
        return {"message": "Product deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{product_id}/stock")
async def update_product_stock(
    product_id: int,
    quantity: int,
    increment: bool = True,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update product stock (requires products:update permission)."""
    if not has_permission(current_user, "products:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    product_service = ProductService(db)
    try:
        product = product_service.update_stock(product_id, quantity, increment)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Category endpoints
@router.get("/categories/", response_model=List[Category])
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    parent_id: Optional[int] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get categories (requires products:read permission)."""
    if not has_permission(current_user, "products:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    category_service = CategoryService(db)
    categories = category_service.get_categories(skip=skip, limit=limit, parent_id=parent_id)
    return categories


@router.get("/categories/tree")
async def get_category_tree(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category tree structure (requires products:read permission)."""
    if not has_permission(current_user, "products:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    category_service = CategoryService(db)
    tree = category_service.get_category_tree()
    return tree


@router.get("/categories/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category by ID (requires products:read permission)."""
    if not has_permission(current_user, "products:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    category_service = CategoryService(db)
    category = category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/categories/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new category (requires products:create permission)."""
    if not has_permission(current_user, "products:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    category_service = CategoryService(db)
    try:
        category = category_service.create_category(category_data)
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update category (requires products:update permission)."""
    if not has_permission(current_user, "products:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    category_service = CategoryService(db)
    try:
        category = category_service.update_category(category_id, category_data)
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete category (requires products:delete permission)."""
    if not has_permission(current_user, "products:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    category_service = CategoryService(db)
    try:
        category_service.delete_category(category_id)
        return {"message": "Category deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
