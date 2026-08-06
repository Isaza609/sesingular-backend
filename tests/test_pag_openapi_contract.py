"""Contrato Swagger de la Épica 10 (Pagos). Corre sobre el harness liviano (SQLite)."""

from __future__ import annotations


def test_pag_openapi_contract_documents_payment_endpoints(api_context):
    client, _db, _auth, _token_for = api_context
    spec = client.get("/api/v1/openapi.json")
    if spec.status_code == 404:
        spec = client.get("/openapi.json")
    assert spec.status_code == 200
    doc = spec.json()
    paths = doc["paths"]
    schemas = doc["components"]["schemas"]

    hu_by_path = {
        ("/api/v1/catalog/stores/{store_id}/payment-options", "get"): "HU-PAG-01",
        ("/api/v1/payments/orders/{order_id}/intent", "post"): "HU-PAG-02",
        ("/api/v1/payments/webhooks/{provider}", "post"): "HU-PAG-02",
        ("/api/v1/seller/payout-accounts", "get"): "HU-PAG-03",
        ("/api/v1/seller/payout-accounts", "post"): "HU-PAG-03",
        ("/api/v1/seller/payout-accounts/{account_id}", "delete"): "HU-PAG-04",
        ("/api/v1/orders/{order_id}/payment", "get"): "HU-PAG-05",
        ("/api/v1/orders/{order_id}/payment/receipt", "post"): "HU-PAG-05",
        ("/api/v1/seller/payments", "get"): "HU-PAG-06",
        ("/api/v1/seller/payments/{payment_id}/confirm", "post"): "HU-PAG-06",
        ("/api/v1/seller/payments/{payment_id}/reject", "post"): "HU-PAG-06",
        ("/api/v1/seller/payments/{payment_id}/reopen", "post"): "HU-PAG-07",
        ("/api/v1/seller/payments/{payment_id}/overpaid", "post"): "HU-PAG-07",
        ("/api/v1/admin/transactions", "get"): "HU-PAG-09",
        ("/api/v1/admin/transactions/{payment_id}", "get"): "HU-PAG-09",
    }

    for (path, method), hu in hu_by_path.items():
        assert path in paths, f"Falta ruta {path}"
        operation = paths[path][method]
        assert operation.get("summary"), f"{path} sin summary"
        assert hu in operation["description"], f"{path} sin referencia {hu}"
        assert operation.get("responses"), f"{path} sin responses"
        assert "200" in operation["responses"] or "201" in operation["responses"]

    for schema in [
        "PaymentOut",
        "PaymentIntentOut",
        "WebhookResultOut",
        "SellerPaymentOut",
        "PayoutAccountOut",
        "PaymentIncompleteIn",
        "PaymentOverpaidIn",
        "TransactionOut",
        "TransactionEventOut",
        "TransactionListOut",
    ]:
        assert schema in schemas, f"Falta schema {schema}"
