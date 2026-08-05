from app.models import User
from app.models.user import UserRole


def test_hu_usr_01_register_buyer_success(api_context):
    client, db, _auth, _token_for = api_context

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "comprador@example.com",
            "password": "CompraSegura123",
            "name": "Ana Perez",
            "phone": "+573001112233",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user"]["role"] == "buyer"
    user = db.get(User, data["user"]["id"])
    assert user.email == "comprador@example.com"
    assert user.role == UserRole.buyer


def test_hu_usr_01_register_duplicate_email_is_rejected(api_context):
    client, db, _auth, _token_for = api_context
    db.add(User(id="buyer-1", email="comprador@example.com", name="Ana", role=UserRole.buyer))
    db.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "comprador@example.com", "password": "CompraSegura123", "name": "Ana Perez"},
    )

    assert response.status_code == 409
    assert "registrado" in response.json()["detail"]


def test_hu_usr_01_public_register_does_not_accept_seller_role(api_context):
    client, _db, _auth, _token_for = api_context

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "seller@example.com",
            "password": "CompraSegura123",
            "name": "Seller",
            "role": "seller",
        },
    )

    assert response.status_code == 422


def test_hu_usr_01_login_invalid_credentials_do_not_reveal_field(api_context):
    client, _db, auth, _token_for = api_context
    auth.fail_login = True

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "comprador@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales invalidas"
