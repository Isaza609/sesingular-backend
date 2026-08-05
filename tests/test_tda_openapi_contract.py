from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/seller/store", "get"): "HU-TDA-01",
    ("/api/v1/seller/store", "patch"): "HU-TDA-01",
    ("/api/v1/catalog/stores", "get"): "HU-TDA-01",
    ("/api/v1/seller/warehouses", "get"): "HU-TDA-02",
    ("/api/v1/seller/warehouses", "post"): "HU-TDA-02",
    ("/api/v1/seller/warehouses/{warehouse_id}", "patch"): "HU-TDA-02",
    ("/api/v1/seller/store/settings", "get"): "HU-TDA-03",
    ("/api/v1/seller/store/settings", "put"): "HU-TDA-03",
    ("/api/v1/catalog/stores/{store_id}/payment-options", "get"): "HU-TDA-03",
}


def test_tda_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hu in HU_BY_OPERATION.items():
        operation = paths[path][method]
        assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert "200" in operation["responses"] or "201" in operation["responses"]


def test_tda_private_routes_require_bearer_authentication():
    paths = app.openapi()["paths"]
    private_paths = [
        "/api/v1/seller/store",
        "/api/v1/seller/store/settings",
        "/api/v1/seller/warehouses",
    ]
    for path in private_paths:
        for operation in paths[path].values():
            assert any("HTTPBearer" in security for security in operation.get("security", []))
