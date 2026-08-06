from app.models import Cart, StoreMember, User
from app.models.user import UserRole

from tests.checkout_test_utils import add_cart_item, seed_checkout_store


def test_hu_chk_05_multistore_checkout_splits_orders_and_buyer_sees_grouped_purchase(api_context):
    client, db, _auth, token_for = api_context
    seller_a, buyer, store_a, _product_a, variant_a, address, cart, _wh_a = seed_checkout_store(db, "05a", price=30000)
    seller_b, _buyer, store_b, _product_b, variant_b, _addr_b, cart, _wh_b = seed_checkout_store(db, "05b", buyer=buyer, cart=cart, price=40000)
    team_user = User(id="seller-chk-05-team", email="seller-chk-05-team@example.com", name="Team", role=UserRole.seller)
    db.add(team_user)
    db.flush()
    db.add(StoreMember(store_id=store_a.id, user_id=team_user.id, role="operator"))
    add_cart_item(db, cart, variant_a, 1)
    add_cart_item(db, cart, variant_b, 1)
    db.commit()

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    purchase = client.get(f"/api/v1/purchases/{checkout.json()['purchase_id']}", headers=token_for(buyer.id))
    seller_a_orders = client.get("/api/v1/seller/orders", headers=token_for(seller_a.id))
    seller_b_orders = client.get("/api/v1/seller/orders", headers=token_for(seller_b.id))
    team_orders = client.get("/api/v1/seller/orders", headers=token_for(team_user.id))

    assert checkout.status_code == 201
    orders = checkout.json()["orders"]
    assert len(orders) == 2
    assert {order["store_id"] for order in orders} == {store_a.id, store_b.id}
    assert purchase.status_code == 200
    assert len(purchase.json()["store_statuses"]) == 2
    assert seller_a_orders.status_code == 200
    assert [order["store_id"] for order in seller_a_orders.json()] == [store_a.id]
    assert seller_b_orders.status_code == 200
    assert [order["store_id"] for order in seller_b_orders.json()] == [store_b.id]
    assert team_orders.status_code == 200
    assert [order["store_id"] for order in team_orders.json()] == [store_a.id]


def test_hu_chk_05_other_buyer_cannot_read_grouped_purchase(api_context):
    client, db, _auth, token_for = api_context
    _seller, buyer, _store, _product, variant, address, cart, _wh = seed_checkout_store(db, "05c")
    other = User(id="buyer-chk-05-other", email="buyer-chk-05-other@example.com", name="Other", role=UserRole.buyer)
    db.add_all([other, Cart(id="cart-chk-05-other", user_id=other.id)])
    add_cart_item(db, cart, variant, 1)
    db.commit()

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    forbidden = client.get(f"/api/v1/purchases/{checkout.json()['purchase_id']}", headers=token_for(other.id))

    assert checkout.status_code == 201
    assert forbidden.status_code == 404
