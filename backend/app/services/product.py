from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.product import Product, Category, product_category as ProductCategory
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilter, CategoryCreate, CategoryUpdate
import json


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_products(self, filters: ProductFilter) -> List[Product]:
        """Get products with complex filtering."""
        query = self.db.query(Product)
        
        # Search across multiple fields
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                (Product.name.ilike(search_term)) |
                (Product.description.ilike(search_term)) |
                (Product.sku.ilike(search_term))
            )
        
        # Status filter
        if filters.status:
            query = query.filter(Product.status == filters.status)
        
        # Category filter
        if filters.category_id:
            query = query.join(ProductCategory).filter(
                ProductCategory.c.category_id == filters.category_id
            )
        
        # Featured filter
        if filters.is_featured is not None:
            query = query.filter(Product.is_featured == filters.is_featured)
        
        # Digital filter
        if filters.is_digital is not None:
            query = query.filter(Product.is_digital == filters.is_digital)
        
        # Price range filter
        if filters.min_price is not None:
            query = query.filter(Product.price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.filter(Product.price <= filters.max_price)
        
        # Stock filter
        if filters.in_stock is not None:
            if filters.in_stock:
                query = query.filter(Product.stock_quantity > 0)
            else:
                query = query.filter(Product.stock_quantity == 0)
        
        # Low stock alert
        query = query.filter(
            Product.stock_quantity <= Product.low_stock_threshold
        )
        
        return query.offset(filters.skip).limit(filters.limit).all()

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_product_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug."""
        return self.db.query(Product).filter(Product.slug == slug).first()

    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self.db.query(Product).filter(Product.sku == sku).first()

    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        # Check if slug exists
        if self.get_product_by_slug(product_data.slug):
            raise ValueError("Product slug already exists")
        
        # Check if SKU exists
        if product_data.sku and self.get_product_by_sku(product_data.sku):
            raise ValueError("Product SKU already exists")
        
        db_product = Product(
            name=product_data.name,
            slug=product_data.slug,
            description=product_data.description,
            sku=product_data.sku,
            price=product_data.price,
            compare_price=product_data.compare_price,
            stock_quantity=product_data.stock_quantity,
            low_stock_threshold=product_data.low_stock_threshold,
            weight=product_data.weight,
            dimensions=product_data.dimensions,
            image_url=product_data.image_url,
            images=product_data.images,
            status=product_data.status,
            is_featured=product_data.is_featured,
            is_digital=product_data.is_digital,
            meta_title=product_data.meta_title,
            meta_description=product_data.meta_description,
        )
        
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        
        # Add categories
        if product_data.category_ids:
            for category_id in product_data.category_ids:
                category = self.db.query(Category).filter(Category.id == category_id).first()
                if category:
                    db_product.categories.append(category)
            self.db.commit()
            self.db.refresh(db_product)
        
        return db_product

    def update_product(self, product_id: int, product_data: ProductUpdate) -> Product:
        """Update product."""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        update_data = product_data.model_dump(exclude_unset=True)
        
        # Check slug uniqueness if updating
        if "slug" in update_data:
            existing = self.get_product_by_slug(update_data["slug"])
            if existing and existing.id != product_id:
                raise ValueError("Product slug already exists")
        
        # Check SKU uniqueness if updating
        if "sku" in update_data and update_data["sku"]:
            existing = self.get_product_by_sku(update_data["sku"])
            if existing and existing.id != product_id:
                raise ValueError("Product SKU already exists")
        
        for field, value in update_data.items():
            if field != "category_ids":
                setattr(product, field, value)
        
        # Update categories if provided
        if "category_ids" in update_data:
            product.categories.clear()
            for category_id in update_data["category_ids"]:
                category = self.db.query(Category).filter(Category.id == category_id).first()
                if category:
                    product.categories.append(category)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product

    def delete_product(self, product_id: int) -> bool:
        """Delete product."""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        self.db.delete(product)
        self.db.commit()
        
        return True

    def update_stock(self, product_id: int, quantity: int, increment: bool = True) -> Product:
        """Update product stock quantity."""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        if increment:
            product.stock_quantity += quantity
        else:
            if product.stock_quantity < quantity:
                raise ValueError("Insufficient stock")
            product.stock_quantity -= quantity
        
        self.db.commit()
        self.db.refresh(product)
        
        return product

    def get_low_stock_products(self, threshold: Optional[int] = None) -> List[Product]:
        """Get products with low stock."""
        query = self.db.query(Product)
        
        if threshold:
            query = query.filter(Product.stock_quantity <= threshold)
        else:
            query = query.filter(
                Product.stock_quantity <= Product.low_stock_threshold
            )
        
        return query.all()


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_categories(self, skip: int = 0, limit: int = 100, parent_id: Optional[int] = None) -> List[Category]:
        """Get categories with optional parent filter."""
        query = self.db.query(Category)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        
        return query.offset(skip).limit(limit).all()

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return self.db.query(Category).filter(Category.slug == slug).first()

    def create_category(self, category_data: CategoryCreate) -> Category:
        """Create a new category."""
        # Check if slug exists
        if self.get_category_by_slug(category_data.slug):
            raise ValueError("Category slug already exists")
        
        # Check if parent exists
        if category_data.parent_id:
            parent = self.get_category_by_id(category_data.parent_id)
            if not parent:
                raise ValueError("Parent category not found")
        
        db_category = Category(
            name=category_data.name,
            slug=category_data.slug,
            description=category_data.description,
            parent_id=category_data.parent_id,
            image_url=category_data.image_url,
            is_active=category_data.is_active,
        )
        
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        
        return db_category

    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Category:
        """Update category."""
        category = self.get_category_by_id(category_id)
        if not category:
            raise ValueError("Category not found")
        
        update_data = category_data.model_dump(exclude_unset=True)
        
        # Check slug uniqueness if updating
        if "slug" in update_data:
            existing = self.get_category_by_slug(update_data["slug"])
            if existing and existing.id != category_id:
                raise ValueError("Category slug already exists")
        
        # Check parent if updating
        if "parent_id" in update_data and update_data["parent_id"]:
            parent = self.get_category_by_id(update_data["parent_id"])
            if not parent:
                raise ValueError("Parent category not found")
            if parent.id == category_id:
                raise ValueError("Category cannot be its own parent")
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        self.db.commit()
        self.db.refresh(category)
        
        return category

    def delete_category(self, category_id: int) -> bool:
        """Delete category."""
        category = self.get_category_by_id(category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Check if category has children
        children = self.db.query(Category).filter(Category.parent_id == category_id).first()
        if children:
            raise ValueError("Cannot delete category with child categories")
        
        self.db.delete(category)
        self.db.commit()
        
        return True

    def get_category_tree(self) -> List[dict]:
        """Get category tree structure."""
        categories = self.db.query(Category).filter(Category.parent_id.is_(None)).all()
        
        def build_tree(category):
            return {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "image_url": category.image_url,
                "is_active": category.is_active,
                "children": [build_tree(child) for child in category.parent]
            }
        
        return [build_tree(cat) for cat in categories]
