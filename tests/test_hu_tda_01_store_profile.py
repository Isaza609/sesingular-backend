from app.models import Store, StoreMember, User
from app.models.user import UserRole


def _seller_store(db):
    seller = User(id="seller-tda-01", email="seller-tda-01@example.com", name="Seller TDA", role=UserRole.seller)
    store = Store(id="store-tda-01", slug="nova", name="Nova Ropa", social_links={})
    db.add_all([seller, store])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store


def test_hu_tda_01_seller_updates_public_contact_and_catalog_reflects(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db)

    response = client.patch(
        "/api/v1/seller/store",
        headers=token_for(seller.id),
        json={
            "description": "Joyeria hecha a mano.",
            "logo_url": "https://cdn.example.com/nova/logo.png",
            "contact_email": "hola@nova.example",
            "contact_phone": "+573001112233",
            "whatsapp_phone": "+573009998877",
            "social_links": {"instagram": "https://instagram.com/nova"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Nova Ropa"
    assert body["contact_email"] == "hola@nova.example"
    assert body["whatsapp_phone"] == "+573009998877"
    assert body["social_links"] == {"instagram": "https://instagram.com/nova"}

    public = client.get("/api/v1/catalog/stores")
    assert public.status_code == 200
    item = next(row for row in public.json()["items"] if row["id"] == store.id)
    assert item["description"] == "Joyeria hecha a mano."
    assert item["logo_url"] == "https://cdn.example.com/nova/logo.png"
    assert item["contact_phone"] == "+573001112233"
    assert item["social_links"]["instagram"] == "https://instagram.com/nova"


def test_hu_tda_01_seller_cannot_change_admin_managed_fields(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db)

    response = client.patch(
        "/api/v1/seller/store",
        headers=token_for(seller.id),
        json={"name": "Nombre legal cambiado", "description": "Nueva descripcion"},
    )

    assert response.status_code == 400
    assert "administracion" in response.json()["detail"]
    db.refresh(store)
    assert store.name == "Nova Ropa"


def test_hu_tda_01_invalid_social_link_points_to_field(api_context):
    client, db, _auth, token_for = api_context
    seller, _store = _seller_store(db)

    response = client.patch(
        "/api/v1/seller/store",
        headers=token_for(seller.id),
        json={"social_links": {"instagram": "instagram.com/nova"}},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "social_links"
