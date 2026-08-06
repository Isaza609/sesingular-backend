"""Contrato Swagger de la Épica 11 (Facturación). Corre sobre el harness liviano (SQLite)."""

from __future__ import annotations


def test_fac_openapi_contract(api_context):
    client, _db, _auth, _token_for = api_context
    spec = client.get("/api/v1/openapi.json")
    if spec.status_code == 404:
        spec = client.get("/openapi.json")
    assert spec.status_code == 200
    doc = spec.json()
    paths = doc["paths"]
    schemas = doc["components"]["schemas"]

    hu_by_path = {
        ("/api/v1/orders/{order_id}/invoice", "get"): "HU-FAC-01",
        ("/api/v1/orders/{order_id}/invoice/download", "get"): "HU-FAC-01",
        ("/api/v1/seller/store", "get"): "HU-FAC-02",
        ("/api/v1/seller/invoices", "get"): "HU-FAC-03",
        ("/api/v1/seller/invoices/{invoice_id}", "get"): "HU-FAC-03",
        ("/api/v1/seller/invoices/{invoice_id}/download", "get"): "HU-FAC-03",
    }
    for (path, method), hu in hu_by_path.items():
        assert path in paths, f"Falta ruta {path}"
        op = paths[path][method]
        assert op.get("summary"), f"{path} sin summary"
        assert hu in op["description"], f"{path} sin referencia {hu}"
        assert op.get("responses")

    for schema in ["InvoiceOut", "InvoiceItemOut", "InvoiceChargeOut", "InvoiceListItemOut"]:
        assert schema in schemas, f"Falta schema {schema}"
