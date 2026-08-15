from fastapi import HTTPException, status
from functools import wraps
from typing import List, Callable
from app.schemas.user import UserRoleEnum
from app.models.user import User


# Role hierarchy and permissions
ROLE_PERMISSIONS = {
    UserRoleEnum.ADMIN: [
        "users:read", "users:create", "users:update", "users:delete",
        "customers:read", "customers:create", "customers:update", "customers:delete",
        "products:read", "products:create", "products:update", "products:delete",
        "orders:read", "orders:create", "orders:update", "orders:delete",
        "subscriptions:read", "subscriptions:create", "subscriptions:update", "subscriptions:delete",
        "invoices:read", "invoices:create", "invoices:update", "invoices:delete",
        "plans:read", "plans:create", "plans:update", "plans:delete",
        "analytics:read",
        "audit:read",
        "impersonate:users",
        "export:data"
    ],
    UserRoleEnum.MANAGER: [
        "customers:read", "customers:create", "customers:update",
        "products:read", "products:create", "products:update",
        "orders:read", "orders:create", "orders:update",
        "subscriptions:read", "subscriptions:create", "subscriptions:update",
        "invoices:read", "invoices:create",
        "plans:read",
        "analytics:read",
        "export:data"
    ],
    UserRoleEnum.SUPPORT: [
        "customers:read",
        "products:read",
        "orders:read", "orders:update",
        "subscriptions:read",
        "invoices:read",
        "analytics:read"
    ],
    UserRoleEnum.CUSTOMER: [
        "customers:read",
        "products:read",
        "orders:read",
        "subscriptions:read",
        "invoices:read"
    ]
}


def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    if user.is_superuser:
        return True
    
    user_permissions = set()
    for role in user.roles:
        role_name = role.name.lower()
        if role_name in ROLE_PERMISSIONS:
            user_permissions.update(ROLE_PERMISSIONS[role_name])
    
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[str]) -> bool:
    """Check if user has any of the specified permissions."""
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[str]) -> bool:
    """Check if user has all of the specified permissions."""
    return all(has_permission(user, perm) for perm in permissions)


def require_permission(permission: str):
    """Decorator to require a specific permission."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: UserRoleEnum):
    """Decorator to require a specific role."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            user_roles = [r.name.lower() for r in current_user.roles]
            if role.value not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role.value}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(*roles: UserRoleEnum):
    """Decorator to require any of the specified roles."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            user_roles = [r.name.lower() for r in current_user.roles]
            required_roles = [role.value for role in roles]
            
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of roles {required_roles} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
