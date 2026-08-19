from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def get_customers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[Customer]:
        query = self.db.query(Customer).options(joinedload(Customer.user))

        if search:
            term = f"%{search}%"
            query = query.join(User).filter(
                (Customer.company_name.ilike(term))
                | (User.full_name.ilike(term))
                | (User.email.ilike(term))
                | (Customer.city.ilike(term))
                | (Customer.industry.ilike(term))
            )

        return query.offset(skip).limit(limit).all()

    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.db.query(Customer).options(joinedload(Customer.user)).filter(Customer.id == customer_id).first()

    def get_customer_by_user_id(self, user_id: int) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.user_id == user_id).first()

    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        user = self.db.query(User).filter(User.id == customer_data.user_id).first()
        if not user:
            raise ValueError("User not found")

        existing = self.get_customer_by_user_id(customer_data.user_id)
        if existing:
            raise ValueError("Customer already exists for this user")

        db_customer = Customer(**customer_data.model_dump())
        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer

    def update_customer(self, customer_id: int, customer_data: CustomerUpdate) -> Customer:
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            raise ValueError("Customer not found")

        update_data = customer_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete_customer(self, customer_id: int) -> bool:
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            raise ValueError("Customer not found")

        self.db.delete(customer)
        self.db.commit()
        return True
