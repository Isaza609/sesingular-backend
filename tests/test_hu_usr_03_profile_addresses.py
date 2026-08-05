from app.models import Address, User
from app.models.user import UserRole


def test_hu_usr_03_patch_profile_updates_contact_data(api_context):
    client, db, _auth, token_for = api_context
    buyer = User(id="buyer-1", email="buyer@example.com", name="Ana", role=UserRole.buyer)
    db.add(buyer)
    db.commit()

    response = client.patch(
        "/api/v1/auth/me",
        json={"name": "Ana Maria", "phone": "+573004445566"},
        headers=token_for(buyer.id),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Ana Maria"
    assert response.json()["phone"] == "+573004445566"


def test_hu_usr_03_buyer_address_crud_and_default_selection(api_context):
    client, db, _auth, token_for = api_context
    buyer = User(id="buyer-1", email="buyer@example.com", name="Ana", role=UserRole.buyer)
    db.add(buyer)
    db.commit()
    headers = token_for(buyer.id)

    first = client.post(
        "/api/v1/addresses",
        json={
            "label": "Casa",
            "recipient_name": "Ana Perez",
            "address_line": "Calle 10 # 20-30",
            "city": "Bogota",
            "is_default": True,
        },
        headers=headers,
    )
    second = client.post(
        "/api/v1/addresses",
        json={
            "label": "Oficina",
            "recipient_name": "Ana Perez",
            "address_line": "Carrera 15 # 80-20",
            "city": "Medellin",
            "is_default": True,
        },
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    first_address = db.get(Address, first.json()["id"])
    assert first_address.is_default is False
    listed = client.get("/api/v1/addresses", headers=headers)
    assert listed.status_code == 200
    assert [row["label"] for row in listed.json()] == ["Oficina", "Casa"]
    patched = client.patch(
        f"/api/v1/addresses/{second.json()['id']}",
        json={"city": "Envigado"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["city"] == "Envigado"
    deleted = client.delete(f"/api/v1/addresses/{second.json()['id']}", headers=headers)
    assert deleted.status_code == 204


def test_hu_usr_03_required_address_fields_are_validated(api_context):
    client, db, _auth, token_for = api_context
    buyer = User(id="buyer-1", email="buyer@example.com", name="Ana", role=UserRole.buyer)
    db.add(buyer)
    db.commit()

    response = client.post(
        "/api/v1/addresses",
        json={"recipient_name": "", "address_line": "", "city": ""},
        headers=token_for(buyer.id),
    )

    assert response.status_code == 422


def test_hu_usr_03_buyer_cannot_update_another_users_address(api_context):
    client, db, _auth, token_for = api_context
    buyer = User(id="buyer-1", email="buyer@example.com", name="Ana", role=UserRole.buyer)
    other = User(id="buyer-2", email="other@example.com", name="Otra", role=UserRole.buyer)
    address = Address(user_id=other.id, recipient_name="Otra", address_line="Calle 1", city="Cali")
    db.add_all([buyer, other, address])
    db.commit()

    response = client.patch(
        f"/api/v1/addresses/{address.id}",
        json={"city": "Bogota"},
        headers=token_for(buyer.id),
    )

    assert response.status_code == 404
