from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.user import UserCreate, User, Token, LoginRequest, OAuthCallback
from app.services.auth import AuthService
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User as UserModel
from app.models.audit import AuditLog, AuditActionEnum
import httpx
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        auth_service = AuthService(db)
        user = auth_service.register_user(user_data)
        
        # Log audit
        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.CREATE,
            entity_type="user",
            entity_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description="User registered"
        )
        db.add(audit_log)
        db.commit()
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with email and password."""
    try:
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        tokens = auth_service.create_tokens(user)
        
        # Log audit
        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.LOGIN,
            entity_type="user",
            entity_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description="User logged in"
        )
        db.add(audit_log)
        db.commit()
        
        tokens["user"] = user
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token."""
    try:
        auth_service = AuthService(db)
        access_token = auth_service.refresh_access_token(refresh_token)
        
        # Get user from token
        from app.core.security import decode_token
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout current user."""
    # Log audit
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditActionEnum.LOGOUT,
        entity_type="user",
        entity_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        request_path=str(request.url.path),
        description="User logged out"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/google/login")
async def google_login():
    """Get Google OAuth URL."""
    return {
        "auth_url": (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile"
        )
    }


@router.post("/google/callback", response_model=Token)
async def google_callback(
    callback_data: OAuthCallback,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback."""
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": callback_data.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error"])
        
        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_info = user_response.json()
    
    try:
        auth_service = AuthService(db)
        user = auth_service.oauth_login_or_register(
            provider="google",
            provider_id=user_info["id"],
            email=user_info["email"],
            full_name=user_info.get("name")
        )
        tokens = auth_service.create_tokens(user)
        
        # Log audit
        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.LOGIN,
            entity_type="user",
            entity_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description="User logged in via Google OAuth"
        )
        db.add(audit_log)
        db.commit()
        
        tokens["user"] = user
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/github/login")
async def github_login():
    """Get GitHub OAuth URL."""
    return {
        "auth_url": (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={settings.GITHUB_CLIENT_ID}&"
            f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
            f"scope=user:email"
        )
    }


@router.post("/github/callback", response_model=Token)
async def github_callback(
    callback_data: OAuthCallback,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback."""
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": callback_data.code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_REDIRECT_URI
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error"])
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_info = user_response.json()
        
        # Get user email
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        emails = email_response.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), None)
    
    if not primary_email:
        raise HTTPException(status_code=400, detail="No primary email found")
    
    try:
        auth_service = AuthService(db)
        user = auth_service.oauth_login_or_register(
            provider="github",
            provider_id=str(user_info["id"]),
            email=primary_email,
            full_name=user_info.get("name")
        )
        tokens = auth_service.create_tokens(user)
        
        # Log audit
        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.LOGIN,
            entity_type="user",
            entity_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            description="User logged in via GitHub OAuth"
        )
        db.add(audit_log)
        db.commit()
        
        tokens["user"] = user
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
