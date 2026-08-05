from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/catalog/products", "get"): "HU-PROM-01",
    ("/api/v1/catalog/products/{slug}", "get"): "HU-PROM-01",
    ("/api/v1/seller/products", "get"): "HU-PROM-03",
    ("/api/v1/seller/variants/{variant_id}", "patch"): "HU-PROM-01",
    ("/api/v1/seller/promotions", "get"): "HU-PROM-02",
    ("/api/v1/seller/promotions", "post"): "HU-PROM-02",
    ("/api/v1/seller/promotions/{promotion_id}", "patch"): "HU-PROM-02",
    ("/api/v1/seller/promotions/{promotion_id}", "delete"): "HU-PROM-02",
    ("/api/v1/seller/coupons", "get"): "HU-PROM-02",
    ("/api/v1/seller/coupons", "post"): "HU-PROM-02",
    ("/api/v1/seller/coupons/{coupon_id}", "patch"): "HU-PROM-02",
    ("/api/v1/seller/coupons/{coupon_id}", "delete"): "HU-PROM-02",
    ("/api/v1/seller/extra-charges", "get"): "HU-PROM-04",
    ("/api/v1/seller/extra-charges", "post"): "HU-PROM-04",
    ("/api/v1/seller/extra-charges/{charge_id}", "patch"): "HU-PROM-04",
    ("/api/v1/seller/extra-charges/{charge_id}", "delete"): "HU-PROM-04",
    ("/api/v1/checkout/quote", "post"): "HU-PROM-04",
    ("/api/v1/checkout", "post"): "HU-PROM-04",
}


PRIVATE_PATHS = [
    "/api/v1/seller/products",
    "/api/v1/seller/promotions",
    "/api/v1/seller/coupons",
    "/api/v1/seller/extra-charges",
    "/api/v1/checkout/quote",
    "/api/v1/checkout",
]


def test_prom_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hu in HU_BY_OPERATION.items():
        operation = paths[path][method]
        assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert "200" in operation["responses"] or "201" in operation["responses"]


def test_prom_private_routes_require_bearer_authentication():
    paths = app.openapi()["paths"]
    for path in PRIVATE_PATHS:
        for operation in paths[path].values():
            assert any("HTTPBearer" in security for security in operation.get("security", []))
