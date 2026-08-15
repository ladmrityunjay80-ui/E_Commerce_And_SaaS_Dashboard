import pytest
from app.core.rbac import has_permission, has_any_permission, has_all_permissions
from app.models.user import User, Role
from app.schemas.user import UserRoleEnum


def test_has_permission_superuser():
    """Test that superusers have all permissions."""
    user = User(
        id=1,
        email="admin@example.com",
        is_superuser=True,
        roles=[]
    )
    
    assert has_permission(user, "users:delete") is True
    assert has_permission(user, "any:permission") is True


def test_has_permission_admin():
    """Test admin role permissions."""
    user = User(
        id=1,
        email="admin@example.com",
        is_superuser=False,
        roles=[Role(name="admin", id=1)]
    )
    
    assert has_permission(user, "users:delete") is True
    assert has_permission(user, "users:create") is True
    assert has_permission(user, "analytics:read") is True


def test_has_permission_manager():
    """Test manager role permissions."""
    user = User(
        id=1,
        email="manager@example.com",
        is_superuser=False,
        roles=[Role(name="manager", id=1)]
    )
    
    assert has_permission(user, "users:delete") is False
    assert has_permission(user, "users:create") is False
    assert has_permission(user, "products:create") is True
    assert has_permission(user, "analytics:read") is True


def test_has_permission_support():
    """Test support role permissions."""
    user = User(
        id=1,
        email="support@example.com",
        is_superuser=False,
        roles=[Role(name="support", id=1)]
    )
    
    assert has_permission(user, "users:delete") is False
    assert has_permission(user, "products:create") is False
    assert has_permission(user, "orders:read") is True
    assert has_permission(user, "analytics:read") is True


def test_has_permission_customer():
    """Test customer role permissions."""
    user = User(
        id=1,
        email="customer@example.com",
        is_superuser=False,
        roles=[Role(name="customer", id=1)]
    )
    
    assert has_permission(user, "users:delete") is False
    assert has_permission(user, "products:create") is False
    assert has_permission(user, "orders:read") is True
    assert has_permission(user, "analytics:read") is False


def test_has_any_permission():
    """Test has_any_permission function."""
    user = User(
        id=1,
        email="manager@example.com",
        is_superuser=False,
        roles=[Role(name="manager", id=1)]
    )
    
    assert has_any_permission(user, ["users:delete", "products:create"]) is True
    assert has_any_permission(user, ["users:delete", "users:update"]) is False


def test_has_all_permissions():
    """Test has_all_permissions function."""
    user = User(
        id=1,
        email="manager@example.com",
        is_superuser=False,
        roles=[Role(name="manager", id=1)]
    )
    
    assert has_all_permissions(user, ["products:create", "orders:create"]) is True
    assert has_all_permissions(user, ["products:create", "users:delete"]) is False


def test_multiple_roles():
    """Test user with multiple roles."""
    user = User(
        id=1,
        email="multi@example.com",
        is_superuser=False,
        roles=[
            Role(name="support", id=1),
            Role(name="manager", id=2)
        ]
    )
    
    # Should have permissions from both roles
    assert has_permission(user, "products:create") is True  # From manager
    assert has_permission(user, "orders:read") is True  # From both
    assert has_permission(user, "users:delete") is False  # Neither role
