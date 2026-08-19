import pytest


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "SaaS Admin Dashboard API" in response.json()["message"]


def test_auth_flow(client):
    # Register
    response = client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "password": "password123",
        "full_name": "Test User",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@test.com"

    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "user@test.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_users_crud(auth_client):
    response = auth_client.get("/api/v1/users")
    assert response.status_code == 200

    response = auth_client.post("/api/v1/users", json={
        "email": "newuser@test.com",
        "password": "password123",
        "full_name": "New User",
        "role": "manager",
    })
    assert response.status_code == 201
    user_id = response.json()["id"]

    response = auth_client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200


def test_customers_crud(auth_client):
    response = auth_client.post("/api/v1/users", json={
        "email": "customeruser@test.com",
        "password": "password123",
        "full_name": "Customer User",
        "role": "customer",
    })
    assert response.status_code == 201
    user_id = response.json()["id"]

    response = auth_client.post("/api/v1/customers", json={
        "user_id": user_id,
        "company_name": "Acme Inc",
        "industry": "Software",
    })
    assert response.status_code == 201
    customer_id = response.json()["id"]

    response = auth_client.get(f"/api/v1/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["company_name"] == "Acme Inc"


def test_products_crud(auth_client):
    response = auth_client.post("/api/v1/products", json={
        "name": "Test Product",
        "slug": "test-product",
        "price": 9.99,
        "stock_quantity": 100,
        "status": "active",
        "is_featured": False,
        "is_digital": False,
    })
    assert response.status_code == 201
    product_id = response.json()["id"]

    response = auth_client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"


def test_payment_create_without_keys(auth_client):
    # Requires an existing order, so create product + customer + order
    response = auth_client.post("/api/v1/products", json={
        "name": "Payment Product",
        "slug": "payment-product",
        "price": 10.0,
        "stock_quantity": 1,
        "status": "active",
    })
    assert response.status_code == 201
    product_id = response.json()["id"]

    response = auth_client.post("/api/v1/users", json={
        "email": "ordercustomer@test.com",
        "password": "password123",
        "full_name": "Order Customer",
        "role": "customer",
    })
    assert response.status_code == 201
    customer_id = response.json().get("customer_id")

    # If user creation didn't create customer, create one
    if not customer_id:
        response = auth_client.post("/api/v1/customers", json={
            "user_id": response.json()["id"],
            "company_name": "Order Co",
        })
        assert response.status_code == 201
        customer_id = response.json()["id"]

    response = auth_client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "subtotal": 10.0,
        "total_amount": 10.0,
        "items": [{
            "product_id": product_id,
            "product_name": "Payment Product",
            "quantity": 1,
            "unit_price": 10.0,
            "total_price": 10.0,
        }],
    })
    assert response.status_code == 201
    order_id = response.json()["id"]

    response = auth_client.post("/api/v1/payments/create", json={
        "order_id": order_id,
        "gateway": "stripe",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["gateway"] == "stripe"
