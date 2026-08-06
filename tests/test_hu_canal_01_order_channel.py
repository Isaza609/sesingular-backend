from app.models import Order
from app.models.order import SaleChannel

from tests.inventory_test_utils import add_cart_item, seed_inventory_store


def test_hu_canal_01_checkout_and_pos_set_and_preserve_order_channel(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, _warehouses, buyers = seed_inventory_store(db, "canal-01", warehouses=1, quantity=6)
    buyer, address, cart = buyers[0]
    add_cart_item(db, cart, variant, 1)

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    online_order_id = checkout.json()["orders"][0]["id"]
    confirmed = client.patch(
        f"/api/v1/seller/orders/{online_order_id}/status",
        headers=token_for(seller.id),
        json={"status": "confirmed"},
    )
    pos = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": variant.id, "quantity": 1}], "payment_method": "cash"},
    )

    online_order = db.get(Order, online_order_id)
    presencial_order = db.get(Order, pos.json()["id"])
    assert checkout.status_code == 201
    assert checkout.json()["orders"][0]["channel"] == SaleChannel.online.value
    assert confirmed.status_code == 200
    assert confirmed.json()["channel"] == SaleChannel.online.value
    assert online_order.channel == SaleChannel.online
    assert pos.status_code == 201
    assert pos.json()["channel"] == SaleChannel.presencial.value
    assert presencial_order.channel == SaleChannel.presencial
