from app.models import User
from app.models.user import UserRole


def test_hu_usr_04_request_password_recovery_sends_email_flow(api_context):
    client, _db, auth, _token_for = api_context

    response = client.post(
        "/api/v1/auth/password-recovery/request",
        json={"email": "vendedor@example.com"},
    )

    assert response.status_code == 202
    assert auth.recovery_requests == ["vendedor@example.com"]
    assert "recibira instrucciones" in response.json()["message"]


def test_hu_usr_04_confirm_recovery_with_valid_token_updates_local_state(api_context):
    client, db, auth, _token_for = api_context
    seller = User(id="seller-1", email="vendedor@example.com", name="Seller", role=UserRole.seller, must_change_password=True)
    db.add(seller)
    db.commit()

    response = client.post(
        "/api/v1/auth/password-recovery/confirm",
        json={
            "email": seller.email,
            "recovery_token": "valid-token",
            "new_password": "NuevaClave123",
        },
    )

    assert response.status_code == 200
    assert auth.password_updates == [("valid-token", "NuevaClave123")]
    db.refresh(seller)
    assert seller.must_change_password is False
    assert seller.password_changed_at is not None


def test_hu_usr_04_expired_recovery_token_is_rejected(api_context):
    client, _db, auth, _token_for = api_context
    auth.fail_recovery_confirm = True

    response = client.post(
        "/api/v1/auth/password-recovery/confirm",
        json={"recovery_token": "expired-token", "new_password": "NuevaClave123"},
    )

    assert response.status_code == 401
    assert "Token expirado" in response.json()["detail"]
