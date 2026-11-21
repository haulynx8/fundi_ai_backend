import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.booking import Booking


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------
# 1. Shop Directory Tests
# ---------------------------------------------------------

def test_list_shops_success(client):
    response = client.get("/api/shops/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 6
    assert len(data["shops"]) >= 6

    # Verify shops are ordered by rating descending
    ratings = [s["rating"] for s in data["shops"] if s["rating"] is not None]
    assert ratings == sorted(ratings, reverse=True)

    # Verify essential fields for each shop
    first_shop = data["shops"][0]
    assert "id" in first_shop
    assert "name" in first_shop
    assert "location" in first_shop
    assert "phone" in first_shop
    assert "services" in first_shop
    assert isinstance(first_shop["services"], list)
    assert first_shop["phone_url"].startswith("tel:")
    assert first_shop["booking_url"].startswith("tel:")


def test_list_shops_filter_by_location(client):
    response = client.get("/api/shops/?location=Westlands")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert any("Westlands" in s["location"] for s in data["shops"])


def test_list_shops_filter_by_service(client):
    response = client.get("/api/shops/?service=router")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert any("Router" in s["name"] or any("router" in str(x).lower() for x in s["services"]) for s in data["shops"])


def test_get_single_shop_success(client):
    list_res = client.get("/api/shops/")
    shop_id = list_res.json()["shops"][0]["id"]

    response = client.get(f"/api/shops/{shop_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == shop_id
    assert len(data["name"]) > 0


def test_get_single_shop_not_found(client):
    response = client.get("/api/shops/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------
# 2. Repair Bookings Tests
# ---------------------------------------------------------

def test_create_booking_success(client):
    list_res = client.get("/api/shops/")
    shop_id = list_res.json()["shops"][0]["id"]
    shop_name = list_res.json()["shops"][0]["name"]

    booking_date = (date.today() + timedelta(days=3)).isoformat()
    payload = {
        "user_name": "Amina Mohamed",
        "phone": "+254711223344",
        "shop_id": shop_id,
        "date": booking_date,
        "device_category": "laptop",
        "notes": "Laptop battery drains very quickly, needs inspection.",
    }

    response = client.post("/api/bookings/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["user_name"] == "Amina Mohamed"
    assert data["phone"] == "+254711223344"
    assert data["shop_id"] == shop_id
    assert data["date"] == booking_date
    assert data["status"] == "pending"
    assert data["device_category"] == "laptop"
    assert data["notes"] == "Laptop battery drains very quickly, needs inspection."
    assert data["shop_name"] == shop_name


def test_create_booking_invalid_shop_id(client):
    payload = {
        "user_name": "Kofi Mensah",
        "phone": "+254722334455",
        "shop_id": 99999,
        "date": (date.today() + timedelta(days=2)).isoformat(),
    }
    response = client.post("/api/bookings/", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_create_booking_invalid_phone_short(client):
    payload = {
        "user_name": "Test User",
        "phone": "123",
        "shop_id": 1,
        "date": (date.today() + timedelta(days=2)).isoformat(),
    }
    response = client.post("/api/bookings/", json=payload)
    assert response.status_code == 422


def test_list_bookings_success(client):
    response = client.get("/api/bookings/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert len(data["bookings"]) >= 1


def test_get_single_booking(client):
    list_res = client.get("/api/bookings/")
    booking_id = list_res.json()["bookings"][0]["id"]

    response = client.get(f"/api/bookings/{booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == booking_id
    assert "user_name" in data
    assert "status" in data


def test_update_booking_status(client):
    list_res = client.get("/api/bookings/")
    booking_id = list_res.json()["bookings"][0]["id"]

    response = client.patch(
        f"/api/bookings/{booking_id}/status",
        json={"status": "confirmed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == booking_id
    assert data["status"] == "confirmed"


def test_update_booking_status_not_found(client):
    response = client.patch(
        "/api/bookings/99999/status",
        json={"status": "confirmed"}
    )
    assert response.status_code == 404
