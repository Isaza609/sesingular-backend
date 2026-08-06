from datetime import datetime, timezone

from app.models import Order, PlatformSetting
from app.models.order import OrderStatus, SaleChannel

from tests.inventory_test_utils import add_cart_item, seed_inventory_store


def _checkout_order(client, db, token_for, buyer, address, cart, variant, quantity: int) -> Order:
    add_cart_item(db, cart, variant, quantity)
    response = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    assert response.status_code == 201
    return db.get(Order, response.json()["orders"][0]["id"])


def _pos_order(client, db, token_for, seller, variant, quantity: int) -> Order:
    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": variant.id, "quantity": quantity}], "payment_method": "cash"},
    )
    assert response.status_code == 201
    return db.get(Order, response.json()["id"])


def _channels(report: dict) -> dict:
    return {row["channel"]: row for row in report["by_channel"]}


def test_hu_canal_03_report_separates_channels_sums_and_respects_scope_date_and_cancelled(api_context):
    client, db, _auth, token_for = api_context
    seller, store, _product, variant, _warehouses, buyers = seed_inventory_store(db, "canal-03", warehouses=1, quantity=20)
    buyer, address, cart = buyers[0]
    online = _checkout_order(client, db, token_for, buyer, address, cart, variant, 2)
    presencial = _pos_order(client, db, token_for, seller, variant, 3)

    db.delete(db.get(PlatformSetting, "payment_gateway"))
    db.commit()
    _other_seller, _other_store, _other_product, other_variant, _other_warehouses, _other_buyers = seed_inventory_store(db, "canal-03-other", warehouses=1, quantity=10)
    _pos_order(client, db, token_for, _other_seller, other_variant, 4)

    cancelled = Order(store_id=store.id, channel=SaleChannel.online, status=OrderStatus.cancelled, subtotal=999000, total=999000, created_at=datetime(2026, 8, 15, tzinfo=timezone.utc))
    outside_range = Order(store_id=store.id, channel=SaleChannel.presencial, status=OrderStatus.delivered, subtotal=111000, total=111000, created_at=datetime(2026, 7, 31, tzinfo=timezone.utc))
    online.created_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    presencial.created_at = datetime(2026, 8, 20, tzinfo=timezone.utc)
    db.add_all([cancelled, outside_range])
    db.commit()

    response = client.get(
        "/api/v1/seller/reports/sales",
        headers=token_for(seller.id),
        params={"date_from": "2026-08-01", "date_to": "2026-08-31"},
    )

    data = response.json()
    channels = _channels(data)
    assert response.status_code == 200
    assert channels["online"] == {"channel": "online", "orders": 1, "gross": 20000}
    assert channels["presencial"] == {"channel": "presencial", "orders": 1, "gross": 30000}
    assert data["totals"]["orders"] == 2
    assert data["totals"]["gross"] == 50000


def test_hu_canal_03_report_returns_zero_for_channel_without_sales(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, _warehouses, buyers = seed_inventory_store(db, "canal-03-zero", warehouses=1, quantity=5)
    buyer, address, cart = buyers[0]
    _checkout_order(client, db, token_for, buyer, address, cart, variant, 1)

    response = client.get(
        "/api/v1/seller/reports/sales",
        headers=token_for(seller.id),
        params={"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    channels = _channels(response.json())
    assert response.status_code == 200
    assert channels["online"]["orders"] == 1
    assert channels["online"]["gross"] == 10000
    assert channels["presencial"] == {"channel": "presencial", "orders": 0, "gross": 0}
