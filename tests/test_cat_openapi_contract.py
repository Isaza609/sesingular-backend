from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/catalog/categories", "get"): "HU-CAT-01",
    ("/api/v1/seller/categories", "get"): "HU-CAT-01",
    ("/api/v1/seller/categories", "post"): "HU-CAT-01",
    ("/api/v1/seller/categories/{category_id}", "patch"): "HU-CAT-01",
    ("/api/v1/seller/categories/{category_id}", "delete"): "HU-CAT-01",
    ("/api/v1/catalog/products", "get"): "HU-CAT-02",
    ("/api/v1/seller/products", "post"): "HU-CAT-02",
    ("/api/v1/seller/products/{product_id}", "patch"): "HU-CAT-02",
}


def test_cat_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hu in HU_BY_OPERATION.items():
        operation = paths[path][method]
        success_status = "204" if method == "delete" else ("201" if method == "post" else "200")
        assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert success_status in operation["responses"]
        assert operation.get("responses", {}).get("422")


def test_cat_seller_routes_require_bearer_authentication():
    paths = app.openapi()["paths"]
    private_paths = [
        "/api/v1/seller/categories",
        "/api/v1/seller/categories/{category_id}",
        "/api/v1/seller/products",
        "/api/v1/seller/products/{product_id}",
    ]
    for path in private_paths:
        for operation in paths[path].values():
            if operation.get("description", "").startswith("Rol permitido: seller. HU-CAT"):
                assert any("HTTPBearer" in security for security in operation.get("security", []))


def test_cat_schemas_include_examples_for_requests_and_responses():
    schemas = app.openapi()["components"]["schemas"]
    for schema_name in ("CategoryIn", "CategoryPatch", "ProductIn", "ProductPatch"):
        assert schemas[schema_name].get("example")

    category_out = schemas["CategoryOut"]["properties"]
    assert category_out["parent_id"].get("description")
    assert category_out["slug"].get("description")
    assert category_out["active"].get("description")
