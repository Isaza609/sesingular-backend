from datetime import datetime, timedelta, timezone

from app.models import Store, StoreMember, User
from app.models.user import UserRole


def test_hu_usr_02_first_login_returns_password_change_required(api_context):
    client, db, auth, _token_for = api_context
    seller = User(
        id="seller-1",
        email="seller@example.com",
        name="Seller",
        role=UserRole.seller,
        must_change_password=True,
        temporary_password_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(seller)
    db.commit()
    auth.login_user_id = seller.id

    response = client.post("/api/v1/auth/login", json={"email": seller.email, "password": "Temporal123"})

    assert response.status_code == 200
    assert response.json()["must_change_password"] is True


def test_hu_usr_02_change_password_unlocks_seller_panel(api_context):
    client, db, auth, token_for = api_context
    store = Store(id="store-1", slug="nova", name="Nova Ropa")
    seller = User(id="seller-1", email="seller@example.com", name="Seller", role=UserRole.seller, must_change_password=True)
    db.add_all([store, seller, StoreMember(store_id=store.id, user_id=seller.id, role="owner")])
    db.commit()

    response = client.post(
        "/api/v1/auth/change-password",
        json={"new_password": "NuevaClave123"},
        headers=token_for(seller.id),
    )

    assert response.status_code == 200
    assert response.json()["must_change_password"] is False
    assert auth.updated_passwords == [(seller.id, "NuevaClave123")]
    assert client.get("/api/v1/seller/dashboard", headers=token_for(seller.id)).status_code == 200


def test_hu_usr_02_seller_cannot_skip_password_change(api_context):
    client, db, _auth, token_for = api_context
    store = Store(id="store-1", slug="nova", name="Nova Ropa")
    seller = User(id="seller-1", email="seller@example.com", name="Seller", role=UserRole.seller, must_change_password=True)
    db.add_all([store, seller, StoreMember(store_id=store.id, user_id=seller.id, role="owner")])
    db.commit()

    response = client.get("/api/v1/seller/dashboard", headers=token_for(seller.id))

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "password_change_required"


def test_hu_usr_02_expired_temporary_password_asks_admin_contact(api_context):
    client, db, auth, _token_for = api_context
    seller = User(
        id="seller-1",
        email="seller@example.com",
        name="Seller",
        role=UserRole.seller,
        must_change_password=True,
        temporary_password_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db.add(seller)
    db.commit()
    auth.login_user_id = seller.id

    response = client.post("/api/v1/auth/login", json={"email": seller.email, "password": "Temporal123"})

    assert response.status_code == 403
    assert "administrador" in response.json()["detail"]
