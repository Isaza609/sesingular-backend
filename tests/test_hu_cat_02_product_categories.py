from app.models import Category, Store, StoreMember, User
from app.models.user import UserRole


def _seller_store(db, suffix: str):
    seller = User(
        id=f"seller-prod-cat-{suffix}",
        email=f"seller-prod-cat-{suffix}@example.com",
        name=f"Seller PROD CAT {suffix}",
        role=UserRole.seller,
    )
    store = Store(id=f"store-prod-cat-{suffix}", slug=f"store-prod-cat-{suffix}", name=f"Tienda PROD CAT {suffix}", social_links={})
    db.add_all([seller, store])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store


def _category(db, store_id: str, slug: str, name: str, *, active: bool = True) -> Category:
    category = Category(store_id=store_id, slug=slug, name=name, active=active)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _product_payload(category_ids: list[str], *, name: str = "Aretes Luna") -> dict:
    return {
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "short_desc": "Aretes livianos.",
        "description": "Aretes hechos a mano.",
        "material": "Acero",
        "status": "active",
        "category_ids": category_ids,
        "variants": [{"sku": f"{name.lower().replace(' ', '-')}-sku", "price": 45000, "active": True}],
        "images": [{"url": "https://cdn.example.com/products/aretes-luna.jpg", "alt": name}],
    }


def test_hu_cat_02_product_can_belong_to_multiple_categories(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "multi")
    aretes = _category(db, store.id, "aretes", "Aretes")
    regalos = _category(db, store.id, "regalos", "Regalos")

    response = client.post(
        "/api/v1/seller/products",
        headers=token_for(seller.id),
        json=_product_payload([aretes.id, regalos.id]),
    )

    assert response.status_code == 201
    assigned = {row["id"] for row in response.json()["categories"]}
    assert assigned == {aretes.id, regalos.id}


def test_hu_cat_02_public_filter_finds_product_in_any_assigned_category(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "public-filter")
    aretes = _category(db, store.id, "aretes", "Aretes")
    regalos = _category(db, store.id, "regalos", "Regalos")
    product = client.post(
        "/api/v1/seller/products",
        headers=token_for(seller.id),
        json=_product_payload([aretes.id, regalos.id]),
    ).json()

    by_aretes = client.get("/api/v1/catalog/products", params={"store_id": store.id, "category": aretes.slug})
    by_regalos = client.get("/api/v1/catalog/products", params={"store_id": store.id, "category": regalos.slug})

    assert by_aretes.status_code == 200
    assert by_regalos.status_code == 200
    assert product["id"] in {row["id"] for row in by_aretes.json()["items"]}
    assert product["id"] in {row["id"] for row in by_regalos.json()["items"]}


def test_hu_cat_02_patch_removes_category_assignment(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "remove")
    aretes = _category(db, store.id, "aretes", "Aretes")
    regalos = _category(db, store.id, "regalos", "Regalos")
    product = client.post(
        "/api/v1/seller/products",
        headers=token_for(seller.id),
        json=_product_payload([aretes.id, regalos.id]),
    ).json()

    patched = client.patch(
        f"/api/v1/seller/products/{product['id']}",
        headers=token_for(seller.id),
        json={"category_ids": [aretes.id]},
    )
    by_aretes = client.get("/api/v1/catalog/products", params={"store_id": store.id, "category": aretes.slug})
    by_regalos = client.get("/api/v1/catalog/products", params={"store_id": store.id, "category": regalos.slug})

    assert patched.status_code == 200
    assert {row["id"] for row in patched.json()["categories"]} == {aretes.id}
    assert product["id"] in {row["id"] for row in by_aretes.json()["items"]}
    assert product["id"] not in {row["id"] for row in by_regalos.json()["items"]}


def test_hu_cat_02_rejects_foreign_duplicate_and_inactive_categories(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "invalid")
    _other_seller, other_store = _seller_store(db, "foreign")
    aretes = _category(db, store.id, "aretes", "Aretes")
    inactive = _category(db, store.id, "oculta", "Oculta", active=False)
    foreign = _category(db, other_store.id, "ajena", "Ajena")

    duplicated = client.post(
        "/api/v1/seller/products",
        headers=token_for(seller.id),
        json=_product_payload([aretes.id, aretes.id], name="Producto duplicado"),
    )
    foreign_response = client.post(
        "/api/v1/seller/products",
        headers=token_for(seller.id),
        json=_product_payload([foreign.id], name="Producto ajeno"),
    )
    inactive_response = client.post(
        "/api/v1/seller/products",
        headers=token_for(seller.id),
        json=_product_payload([inactive.id], name="Producto inactivo"),
    )

    assert duplicated.status_code == 400
    assert foreign_response.status_code == 400
    assert inactive_response.status_code == 400
