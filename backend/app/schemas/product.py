from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import enum


class ProductStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    sku: Optional[str] = None
    price: float
    compare_price: Optional[float] = None
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    status: ProductStatusEnum = ProductStatusEnum.DRAFT
    is_featured: bool = False
    is_digital: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductCreate(ProductBase):
    category_ids: Optional[List[int]] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    compare_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    status: Optional[ProductStatusEnum] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    category_ids: Optional[List[int]] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[Category] = []

    class Config:
        from_attributes = True


class ProductFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[ProductStatusEnum] = None
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: Optional[bool] = None
    skip: int = 0
    limit: int = 100
