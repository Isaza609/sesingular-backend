from app.models import InventoryMovement
from app.models.inventory import InventoryReason

from tests.inventory_test_utils import seed_inventory_store


def test_hu_inv_06_inventory_movements_are_auditable_and_filterable(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, product, variant, warehouses, _buyers = seed_inventory_store(db, "06", warehouses=1, quantity=4)
    adjusted = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[0].id, "quantity": 1, "note": "Conteo semanal"},
    )
    movements = client.get(
        "/api/v1/seller/inventory/movements",
        headers=token_for(seller.id),
        params={
            "product_id": product.id,
            "variant_id": variant.id,
            "warehouse_id": warehouses[0].id,
            "reason": "adjust",
            "date_from": "2000-01-01T00:00:00",
            "date_to": "2100-01-01T00:00:00",
        },
    )

    row = movements.json()[0]
    stored = db.query(InventoryMovement).filter(InventoryMovement.variant_id == variant.id).one()
    assert adjusted.status_code == 200
    assert movements.status_code == 200
    assert row["id"] == stored.id
    assert row["product_id"] == product.id
    assert row["delta"] == -3
    assert row["reason"] == InventoryReason.adjust.value
    assert row["note"] == "Conteo semanal"
