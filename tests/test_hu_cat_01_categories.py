from app.models import Category, Store, StoreMember, User
from app.models.user import UserRole


def _seller_store(db, suffix: str):
    seller = User(
        id=f"seller-cat-{suffix}",
        email=f"seller-cat-{suffix}@example.com",
        name=f"Seller CAT {suffix}",
        role=UserRole.seller,
    )
    store = Store(id=f"store-cat-{suffix}", slug=f"store-cat-{suffix}", name=f"Tienda CAT {suffix}", social_links={})
    db.add_all([seller, store])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store


def test_hu_cat_01_seller_creates_root_and_subcategory(api_context):
    client, db, _auth, token_for = api_context
    seller, _store = _seller_store(db, "01")

    root = client.post(
        "/api/v1/seller/categories",
        headers=token_for(seller.id),
        json={"name": "Aretes", "sort_order": 10},
    )

    assert root.status_code == 201
    root_body = root.json()
    assert root_body["slug"] == "aretes"
    assert root_body["parent_id"] is None

    child = client.post(
        "/api/v1/seller/categories",
        headers=token_for(seller.id),
        json={"name": "Dorados", "parent_id": root_body["id"], "sort_order": 20},
    )

    assert child.status_code == 201
    assert child.json()["parent_id"] == root_body["id"]

    listed = client.get("/api/v1/seller/categories", headers=token_for(seller.id))
    assert listed.status_code == 200
    by_name = {row["name"]: row for row in listed.json()}
    assert by_name["Aretes"]["parent_id"] is None
    assert by_name["Dorados"]["parent_id"] == root_body["id"]


def test_hu_cat_01_public_catalog_is_scoped_by_store(api_context):
    client, db, _auth, _token_for = api_context
    _seller, store = _seller_store(db, "scope-a")
    _other_seller, other_store = _seller_store(db, "scope-b")
    db.add_all(
        [
            Category(store_id=store.id, slug="aretes", name="Aretes", active=True),
            Category(store_id=other_store.id, slug="collares", name="Collares", active=True),
        ]
    )
    db.commit()

    response = client.get("/api/v1/catalog/categories", params={"store_id": store.id})

    assert response.status_code == 200
    names = {row["name"] for row in response.json()}
    assert names == {"Aretes"}


def test_hu_cat_01_rejects_parent_from_another_store(api_context):
    client, db, _auth, token_for = api_context
    seller, _store = _seller_store(db, "parent-a")
    _other_seller, other_store = _seller_store(db, "parent-b")
    foreign = Category(store_id=other_store.id, slug="ajena", name="Ajena", active=True)
    db.add(foreign)
    db.commit()

    response = client.post(
        "/api/v1/seller/categories",
        headers=token_for(seller.id),
        json={"name": "Subcategoria", "parent_id": foreign.id},
    )

    assert response.status_code == 400


def test_hu_cat_01_rejects_duplicate_slug_in_same_store(api_context):
    client, db, _auth, token_for = api_context
    seller, _store = _seller_store(db, "dup")

    first = client.post("/api/v1/seller/categories", headers=token_for(seller.id), json={"name": "Aretes"})
    duplicate = client.post("/api/v1/seller/categories", headers=token_for(seller.id), json={"name": "Aretes"})

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_hu_cat_01_rejects_hierarchy_cycles(api_context):
    client, db, _auth, token_for = api_context
    seller, _store = _seller_store(db, "cycle")
    root = client.post("/api/v1/seller/categories", headers=token_for(seller.id), json={"name": "Raiz"}).json()
    child = client.post(
        "/api/v1/seller/categories",
        headers=token_for(seller.id),
        json={"name": "Hija", "parent_id": root["id"]},
    ).json()

    self_parent = client.patch(
        f"/api/v1/seller/categories/{root['id']}",
        headers=token_for(seller.id),
        json={"parent_id": root["id"]},
    )
    descendant_parent = client.patch(
        f"/api/v1/seller/categories/{root['id']}",
        headers=token_for(seller.id),
        json={"parent_id": child["id"]},
    )

    assert self_parent.status_code == 400
    assert descendant_parent.status_code == 400


def test_hu_cat_01_delete_hides_category_from_public_catalog(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db, "delete")
    category = client.post("/api/v1/seller/categories", headers=token_for(seller.id), json={"name": "Regalos"}).json()

    deleted = client.delete(f"/api/v1/seller/categories/{category['id']}", headers=token_for(seller.id))
    public = client.get("/api/v1/catalog/categories", params={"store_id": store.id})

    assert deleted.status_code == 204
    assert all(row["id"] != category["id"] for row in public.json())
