"""Smoke de arranque: la app importa, genera el OpenAPI y las APIs publicas responden sin error."""

from __future__ import annotations


def test_app_imports_and_openapi_generates():
    from app.main import app

    schema = app.openapi()
    assert schema["paths"]
    assert schema["components"]["schemas"]
    # rutas clave de las epicas 10-12 presentes
    for path in [
        "/api/v1/seller/payments",
        "/api/v1/orders/{order_id}/invoice",
        "/api/v1/seller/invoices",
        "/api/v1/seller/orders/{order_id}/cancel",
        "/api/v1/seller/orders/{order_id}/assignee",
        "/api/v1/orders/{order_id}/shipment",
        "/api/v1/seller/orders/{order_id}/shipment",
        "/api/v1/seller/orders/{order_id}/return",
        "/api/v1/admin/transactions",
    ]:
        assert path in schema["paths"], f"Falta {path}"


def test_public_apis_respond_without_error(api_context):
    client, _db, _auth, _token_for = api_context
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/catalog/products").status_code == 200
    assert client.get("/api/v1/catalog/stores").status_code == 200
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
