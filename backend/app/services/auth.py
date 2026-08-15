from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserInDB
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from datetime import datetime
import secrets


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserCreate) -> UserInDB:
        """Register a new user."""
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Check if username already exists
        if user_data.username:
            existing_username = self.db.query(User).filter(User.username == user_data.username).first()
            if existing_username:
                raise ValueError("Username already taken")
        
        # Create new user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            is_verified=False,
        )
        
        # Assign default customer role
        customer_role = self.db.query(Role).filter(Role.name == "customer").first()
        if customer_role:
            db_user.roles.append(customer_role)
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user

    def authenticate_user(self, email: str, password: str) -> UserInDB:
        """Authenticate user with email and password."""
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        if not user.hashed_password:
            raise ValueError("Please use OAuth login or set a password")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user

    def create_tokens(self, user: User) -> dict:
        """Create access and refresh tokens for user."""
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def oauth_login_or_register(self, provider: str, provider_id: str, email: str, full_name: str = None) -> User:
        """Login or register user via OAuth."""
        # Check if user exists with this OAuth provider
        if provider == "google":
            user = self.db.query(User).filter(User.google_id == provider_id).first()
        elif provider == "github":
            user = self.db.query(User).filter(User.github_id == provider_id).first()
        else:
            raise ValueError("Invalid OAuth provider")
        
        if user:
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            return user
        
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            # Link OAuth account to existing user
            if provider == "google":
                existing_user.google_id = provider_id
            elif provider == "github":
                existing_user.github_id = provider_id
            existing_user.last_login = datetime.utcnow()
            existing_user.is_verified = True
            self.db.commit()
            self.db.refresh(existing_user)
            return existing_user
        
        # Create new user
        username = email.split("@")[0] + "_" + secrets.token_hex(4)
        db_user = User(
            email=email,
            username=username,
            full_name=full_name,
            is_active=True,
            is_verified=True,
        )
        
        if provider == "google":
            db_user.google_id = provider_id
        elif provider == "github":
            db_user.github_id = provider_id
        
        # Assign default customer role
        customer_role = self.db.query(Role).filter(Role.name == "customer").first()
        if customer_role:
            db_user.roles.append(customer_role)
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user

    def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh access token using refresh token."""
        from app.core.security import decode_token
        
        payload = decode_token(refresh_token)
        if payload is None:
            raise ValueError("Invalid refresh token")
        
        token_type = payload.get("type")
        if token_type != "refresh":
            raise ValueError("Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid refresh token")
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        return create_access_token(data={"sub": user.id})
