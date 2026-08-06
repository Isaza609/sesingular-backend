from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/seller/inventory", "get"): "HU-INV-01",
    ("/api/v1/seller/inventory/{variant_id}", "patch"): "HU-INV-01",
    ("/api/v1/checkout", "post"): "HU-INV-02",
    ("/api/v1/seller/orders/{order_id}/warehouse", "patch"): "HU-INV-03",
    ("/api/v1/seller/orders/{order_id}/status", "patch"): "HU-INV-04",
    ("/api/v1/orders/{order_id}/cancel", "post"): "HU-INV-04",
    ("/api/v1/seller/inventory/alerts", "get"): "HU-INV-05",
    ("/api/v1/seller/inventory/movements", "get"): "HU-INV-06",
    ("/api/v1/cart", "get"): "HU-INV-07",
    ("/api/v1/cart/items", "post"): "HU-INV-07",
    ("/api/v1/catalog/variants/{variant_id}/stock", "get"): "HU-INV-07",
}


PRIVATE_PATHS = [
    "/api/v1/seller/inventory",
    "/api/v1/seller/inventory/{variant_id}",
    "/api/v1/seller/inventory/alerts",
    "/api/v1/seller/inventory/movements",
    "/api/v1/seller/orders/{order_id}/warehouse",
    "/api/v1/seller/orders/{order_id}/status",
    "/api/v1/orders/{order_id}/cancel",
    "/api/v1/cart",
    "/api/v1/cart/items",
    "/api/v1/checkout",
]


def test_inv_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hu in HU_BY_OPERATION.items():
        operation = paths[path][method]
        assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert "200" in operation["responses"] or "201" in operation["responses"]


def test_inv_private_routes_require_bearer_authentication():
    paths = app.openapi()["paths"]
    for path in PRIVATE_PATHS:
        for operation in paths[path].values():
            assert any("HTTPBearer" in security for security in operation.get("security", []))

