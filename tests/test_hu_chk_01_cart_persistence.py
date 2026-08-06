from app.models import StockLevel, User
from app.models.user import UserRole

from tests.checkout_test_utils import seed_checkout_store


def test_hu_chk_01_cart_persists_by_buyer_and_flags_out_of_stock(api_context):
    client, db, _auth, token_for = api_context
    _seller, buyer, _store, _product, variant, _address, _cart, _warehouses = seed_checkout_store(db, "01", quantity=2)
    other = User(id="buyer-chk-01-other", email="buyer-chk-01-other@example.com", name="Other", role=UserRole.buyer)
    db.add(other)
    db.commit()

    created = client.post(
        "/api/v1/cart/items",
        headers=token_for(buyer.id),
        json={"variant_id": variant.id, "quantity": 2},
    )
    same_buyer = client.get("/api/v1/cart", headers=token_for(buyer.id))
    other_buyer = client.get("/api/v1/cart", headers=token_for(other.id))

    level = db.query(StockLevel).filter(StockLevel.variant_id == variant.id).one()
    level.quantity = 0
    db.commit()
    blocked = client.get("/api/v1/cart", headers=token_for(buyer.id))

    assert created.status_code == 200
    assert same_buyer.status_code == 200
    assert same_buyer.json()["items"][0]["variant_id"] == variant.id
    assert same_buyer.json()["items"][0]["available"] is True
    assert other_buyer.status_code == 200
    assert other_buyer.json()["items"] == []
    assert blocked.status_code == 200
    assert blocked.json()["checkout_blocked"] is True
    assert blocked.json()["items"][0]["available"] is False
    assert blocked.json()["items"][0]["availability_status"] == "out_of_stock"


def test_hu_chk_01_patch_delete_and_clear_recalculate_cart(api_context):
    client, db, _auth, token_for = api_context
    _seller, buyer, _store, _product, variant, _address, _cart, _warehouses = seed_checkout_store(db, "01b", price=30000)
    created = client.post("/api/v1/cart/items", headers=token_for(buyer.id), json={"variant_id": variant.id, "quantity": 1})
    item_id = created.json()["items"][0]["id"]

    patched = client.patch(f"/api/v1/cart/items/{item_id}", headers=token_for(buyer.id), json={"quantity": 3})
    deleted = client.delete(f"/api/v1/cart/items/{item_id}", headers=token_for(buyer.id))
    client.post("/api/v1/cart/items", headers=token_for(buyer.id), json={"variant_id": variant.id, "quantity": 1})
    cleared = client.delete("/api/v1/cart", headers=token_for(buyer.id))

    assert patched.status_code == 200
    assert patched.json()["subtotal"] == 90000
    assert deleted.status_code == 200
    assert deleted.json()["items"] == []
    assert cleared.status_code == 200
    assert cleared.json()["items"] == []
