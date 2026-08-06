"""Contrato Swagger de la Épica 12 (Pedidos). Corre sobre el harness liviano (SQLite)."""

from __future__ import annotations


def test_ped_openapi_contract(api_context):
    client, _db, _auth, _token_for = api_context
    spec = client.get("/api/v1/openapi.json")
    if spec.status_code == 404:
        spec = client.get("/openapi.json")
    assert spec.status_code == 200
    doc = spec.json()
    paths = doc["paths"]
    schemas = doc["components"]["schemas"]

    hu_by_path = {
        ("/api/v1/orders", "get"): "HU-PED-03",
        ("/api/v1/seller/orders", "get"): "HU-PED-03",
        ("/api/v1/seller/orders/{order_id}/status", "patch"): "HU-PED-02",
        ("/api/v1/seller/orders/{order_id}/cancel", "post"): "HU-PED-04",
        ("/api/v1/seller/orders/{order_id}/assignee", "patch"): "HU-PED-05",
    }
    for (path, method), hu in hu_by_path.items():
        assert path in paths, f"Falta ruta {path}"
        op = paths[path][method]
        assert op.get("summary"), f"{path} sin summary"
        assert hu in op["description"], f"{path} sin referencia {hu}"
        assert op.get("responses")

    # HU-PED-01: los listados referencian el seguimiento de estado
    assert "HU-PED-01" in paths["/api/v1/orders"]["get"]["description"]
    assert "HU-PED-01" in paths["/api/v1/seller/orders/{order_id}/status"]["patch"]["description"]

    for schema in ["OrderCancelIn", "OrderAssigneeIn"]:
        assert schema in schemas, f"Falta schema {schema}"

    # OrderOut expone responsable y motivo de anulacion
    order_out = schemas["OrderOut"]["properties"]
    assert "assignee_id" in order_out
    assert "cancel_reason" in order_out
