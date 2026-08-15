from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.services.user import UserService
from app.api.deps import get_current_user, get_current_superuser, get_client_ip
from app.models.user import User as UserModel
from app.core.rbac import require_permission, has_permission
from app.models.audit import AuditActionEnum

router = APIRouter()


@router.get("", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (requires users:read permission)."""
    if not has_permission(current_user, "users:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit, search=search, role=role, is_active=is_active)
    return users


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (requires users:read permission)."""
    if not has_permission(current_user, "users:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (requires users:create permission)."""
    if not has_permission(current_user, "users:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.CREATE,
            entity_type="user",
            entity_id=user.id,
            new_values=user_data.model_dump(),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Created user {user.email}"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (requires users:update permission)."""
    if not has_permission(current_user, "users:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    
    # Get old values for audit
    old_user = user_service.get_user_by_id(user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        user = user_service.update_user(user_id, user_data)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.UPDATE,
            entity_type="user",
            entity_id=user_id,
            old_values={"email": old_user.email, "full_name": old_user.full_name, "is_active": old_user.is_active},
            new_values=user_data.model_dump(exclude_unset=True),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Updated user {user.email}"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (requires users:delete permission)."""
    if not has_permission(current_user, "users:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    try:
        user_service.delete_user(user_id)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.DELETE,
            entity_type="user",
            entity_id=user_id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Deleted user {user_id}"
        )
        
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/roles/{role_id}", response_model=User)
async def assign_role(
    user_id: int,
    role_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign role to user (requires users:update permission)."""
    if not has_permission(current_user, "users:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    try:
        user = user_service.assign_role(user_id, role_id)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.UPDATE,
            entity_type="user",
            entity_id=user_id,
            new_values={"role_id": role_id},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Assigned role {role_id} to user {user_id}"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}/roles/{role_id}", response_model=User)
async def remove_role(
    user_id: int,
    role_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove role from user (requires users:update permission)."""
    if not has_permission(current_user, "users:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    try:
        user = user_service.remove_role(user_id, role_id)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.UPDATE,
            entity_type="user",
            entity_id=user_id,
            new_values={"role_id": role_id, "action": "remove"},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Removed role {role_id} from user {user_id}"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/impersonate", response_model=User)
async def impersonate_user(
    user_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Start impersonating a user (requires superuser)."""
    user_service = UserService(db)
    try:
        user = user_service.impersonate_user(current_user.id, user_id)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.IMPERSONATE_START,
            entity_type="user",
            entity_id=user_id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Started impersonating user {user_id}"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/stop-impersonation", response_model=User)
async def stop_impersonation(
    user_id: int,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop impersonating a user."""
    user_service = UserService(db)
    try:
        user = user_service.stop_impersonation(user_id)
        
        # Log audit
        user_service.create_audit_log(
            user_id=current_user.id,
            action=AuditActionEnum.IMPERSONATE_END,
            entity_type="user",
            entity_id=user_id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description=f"Stopped impersonating user {user_id}"
        )
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/audit-logs")
async def get_user_audit_logs(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for a user (requires audit:read permission)."""
    if not has_permission(current_user, "audit:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_service = UserService(db)
    logs = user_service.get_audit_logs(
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        entity_type=entity_type
    )
    return logs
