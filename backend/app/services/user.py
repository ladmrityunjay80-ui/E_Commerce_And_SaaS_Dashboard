from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.core.security import get_password_hash
from app.models.audit import AuditLog, AuditActionEnum
import json


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get users with optional filtering."""
        query = self.db.query(User)
        
        if search:
            query = query.filter(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%")) |
                (User.username.ilike(f"%{search}%"))
            )
        
        if role:
            query = query.join(User.roles).filter(Role.name == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if email exists
        if self.get_user_by_email(user_data.email):
            raise ValueError("Email already registered")
        
        # Check if username exists
        if user_data.username:
            existing = self.db.query(User).filter(User.username == user_data.username).first()
            if existing:
                raise ValueError("Username already taken")
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            is_verified=False,
        )
        
        # Assign requested role or default customer role
        role_name = (user_data.role or "customer").lower()
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if role:
            db_user.roles.append(role)
        else:
            customer_role = self.db.query(Role).filter(Role.name == "customer").first()
            if customer_role:
                db_user.roles.append(customer_role)
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Handle password update separately
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete by setting is_active=False)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.is_active = False
        self.db.commit()
        
        return True

    def assign_role(self, user_id: int, role_id: int) -> User:
        """Assign a role to a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()
            self.db.refresh(user)
        
        return user

    def remove_role(self, user_id: int, role_id: int) -> User:
        """Remove a role from a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        
        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()
            self.db.refresh(user)
        
        return user

    def impersonate_user(self, admin_id: int, target_user_id: int) -> User:
        """Start impersonating a user."""
        admin = self.get_user_by_id(admin_id)
        if not admin or not admin.is_superuser:
            raise ValueError("Only superusers can impersonate")
        
        target_user = self.get_user_by_id(target_user_id)
        if not target_user:
            raise ValueError("Target user not found")
        
        if not target_user.is_active:
            raise ValueError("Cannot impersonate inactive user")
        
        # Set impersonation
        target_user.impersonated_by = admin_id
        self.db.commit()
        self.db.refresh(target_user)
        
        return target_user

    def stop_impersonation(self, user_id: int) -> User:
        """Stop impersonating a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.impersonated_by = None
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def create_audit_log(
        self,
        user_id: int,
        action: AuditActionEnum,
        entity_type: str,
        entity_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_path: Optional[str] = None,
        description: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            description=description
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log

    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering."""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
