from app.models import Category, Store, StoreMember, User
from app.models.user import UserRole


def _seller_store(db, suffix: str):
    seller = User(id=f"seller-prod-01-{suffix}", email=f"seller-prod-01-{suffix}@example.com", name="Seller PROD", role=UserRole.seller)
    store = Store(id=f"store-prod-01-{suffix}", slug=f"store-prod-01-{suffix}", name="Tienda PROD", social_links={})
    db.add_all([seller, store])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store


def _category(db, store_id: str):
    category = Category(store_id=store_id, slug="collares", name="Collares", active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _payload(category_id: str, *, slug: str = "collar-luna") -> dict:
    return {
        "name": "Collar Luna",
        "slug": slug,
        "short_desc": "Collar hecho a mano.",
        "description": "Collar con dije dorado.",
        "status": "active",
        "category_ids": [category_id],
        "variants": [{"sku": f"{slug}-sku", "price": 90000, "cost": 35000}],
        "images": [{"url": "https://cdn.example.com/collar-luna.jpg", "alt": "Collar Luna"}],
    }


def test_hu_prod_01_create_edit_and_discontinue_product(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "crud")
    category = _category(db, store.id)

    created = client.post("/api/v1/seller/products", headers=token_for(seller.id), json=_payload(category.id))
    assert created.status_code == 201
    product = created.json()
    assert product["store_id"] == store.id
    assert product["status"] == "active"

    listed = client.get("/api/v1/seller/products", headers=token_for(seller.id))
    assert product["id"] in {row["id"] for row in listed.json()["items"]}

    patched = client.patch(
        f"/api/v1/seller/products/{product['id']}",
        headers=token_for(seller.id),
        json={"name": "Collar Luna actualizado", "description": "Nueva descripcion"},
    )
    assert patched.status_code == 200

    public = client.get("/api/v1/catalog/products/collar-luna", params={"store_id": store.id})
    assert public.status_code == 200
    assert public.json()["name"] == "Collar Luna actualizado"

    deleted = client.delete(f"/api/v1/seller/products/{product['id']}", headers=token_for(seller.id))
    hidden = client.get("/api/v1/catalog/products/collar-luna", params={"store_id": store.id})
    seller_view = client.get("/api/v1/seller/products", headers=token_for(seller.id), params={"status": "discontinued"})

    assert deleted.status_code == 200
    assert hidden.status_code == 404
    assert product["id"] in {row["id"] for row in seller_view.json()["items"]}


def test_hu_prod_01_rejects_duplicate_slug_and_foreign_scope(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "dup")
    other_seller, other_store = _seller_store(db, "foreign")
    category = _category(db, store.id)
    other_category = Category(store_id=other_store.id, slug="otros", name="Otros", active=True)
    db.add(other_category)
    db.commit()

    first = client.post("/api/v1/seller/products", headers=token_for(seller.id), json=_payload(category.id))
    duplicate = client.post("/api/v1/seller/products", headers=token_for(seller.id), json=_payload(category.id))
    foreign_product = client.post("/api/v1/seller/products", headers=token_for(other_seller.id), json=_payload(other_category.id, slug="ajeno")).json()
    foreign_patch = client.patch(
        f"/api/v1/seller/products/{foreign_product['id']}",
        headers=token_for(seller.id),
        json={"name": "No permitido"},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert foreign_patch.status_code == 404
