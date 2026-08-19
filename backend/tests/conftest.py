import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.core.security import get_password_hash

# Use test database
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def seed_data(db_session):
    """Seed roles and an admin user for integration tests."""
    from app.models.user import User, Role

    roles = ["admin", "manager", "support", "customer"]
    role_objs = {}
    for name in roles:
        role = Role(name=name, description=f"{name.capitalize()} role")
        db_session.add(role)
        db_session.flush()
        role_objs[name] = role

    admin = User(
        email="admin@test.com",
        username="admin",
        full_name="Test Admin",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    admin.roles.append(role_objs["admin"])
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture(scope="function")
def admin_token(client, seed_data):
    """Login and return an admin access token."""
    response = client.post("/api/v1/auth/login", data={
        "username": "admin@test.com",
        "password": "admin123",
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_client(client, admin_token):
    """Test client with admin authorization headers."""
    client.headers = {"Authorization": f"Bearer {admin_token}"}
    return client


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
