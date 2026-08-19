from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging
from app.api.v1 import auth, users, customers, products, orders, subscriptions, invoices, payments, uploads, emails, analytics, websocket

setup_logging()

# Auto-create tables for SQLite/dev convenience; Postgres should use Alembic.
if "sqlite" in settings.DATABASE_URL or settings.ENVIRONMENT == "development":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SaaS Admin Dashboard API",
    description="A full-stack e-commerce and SaaS admin dashboard API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["Uploads"])
app.include_router(emails.router, prefix="/api/v1/emails", tags=["Emails"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])


@app.get("/")
async def root():
    return {
        "message": "SaaS Admin Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
