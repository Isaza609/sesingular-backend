"""Contrato Swagger de la Épica 13 (Envíos). Corre sobre el harness liviano (SQLite)."""

from __future__ import annotations


def test_env_openapi_contract(api_context):
    client, _db, _auth, _token_for = api_context
    spec = client.get("/api/v1/openapi.json")
    if spec.status_code == 404:
        spec = client.get("/openapi.json")
    assert spec.status_code == 200
    doc = spec.json()
    paths = doc["paths"]
    schemas = doc["components"]["schemas"]

    hu_by_path = {
        ("/api/v1/seller/store/settings", "put"): "HU-ENV-01",
        ("/api/v1/orders/{order_id}/shipment", "get"): "HU-ENV-05",
        ("/api/v1/seller/orders/{order_id}/shipment", "patch"): "HU-ENV-05",
        ("/api/v1/seller/orders/{order_id}/return", "post"): "HU-ENV-06",
    }
    for (path, method), hu in hu_by_path.items():
        assert path in paths, f"Falta ruta {path}"
        op = paths[path][method]
        assert op.get("summary"), f"{path} sin summary"
        assert hu in op["description"], f"{path} sin referencia {hu}"
        assert op.get("responses")

    for schema in ["ShipmentOut", "ShipmentEventOut", "ShipmentUpdateIn", "OrderReturnIn"]:
        assert schema in schemas, f"Falta schema {schema}"

    # OrderOut expone contacto y bandera de envio a convenir (HU-ENV-03)
    order_out = schemas["OrderOut"]["properties"]
    assert "shipping_to_agree" in order_out
    assert "store_contact" in order_out
    # ProductOut expone override de envio (HU-ENV-01)
    assert "shipping_mode" in schemas["ProductOut"]["properties"]
