from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/catalog/products", "get"): "HU-PROD",
    ("/api/v1/catalog/products/{slug}", "get"): "HU-PROD",
    ("/api/v1/seller/products", "get"): "HU-PROD-01",
    ("/api/v1/seller/products", "post"): "HU-PROD-01",
    ("/api/v1/seller/products/{product_id}", "patch"): "HU-PROD-01",
    ("/api/v1/seller/products/{product_id}", "delete"): "HU-PROD-01",
    ("/api/v1/seller/products/{product_id}/variants", "post"): "HU-PROD-02",
    ("/api/v1/seller/variants/{variant_id}", "patch"): "HU-PROD-02",
    ("/api/v1/seller/variants/{variant_id}", "delete"): "HU-PROD-02",
    ("/api/v1/seller/products/import/template", "get"): "HU-PROD-03",
    ("/api/v1/seller/products/import", "post"): "HU-PROD-03",
    ("/api/v1/seller/products/{product_id}/images", "post"): "HU-PROD-04",
    ("/api/v1/seller/products/{product_id}/images/{image_id}", "patch"): "HU-PROD-04",
    ("/api/v1/seller/products/{product_id}/images/{image_id}", "delete"): "HU-PROD-04",
}


def test_prod_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hu in HU_BY_OPERATION.items():
        operation = paths[path][method]
        assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert "200" in operation["responses"] or "201" in operation["responses"] or "204" in operation["responses"]
        assert operation.get("responses", {}).get("422")


def test_prod_seller_routes_require_bearer_authentication():
    paths = app.openapi()["paths"]
    for path, operations in paths.items():
        if path.startswith("/api/v1/seller/products") or path.startswith("/api/v1/seller/variants"):
            for operation in operations.values():
                if "HU-PROD" in operation.get("description", ""):
                    assert any("HTTPBearer" in security for security in operation.get("security", []))


def test_prod_schemas_include_examples_and_public_schema_hides_cost():
    schemas = app.openapi()["components"]["schemas"]
    for schema_name in ("ProductIn", "ProductPatch", "VariantIn", "VariantPatch", "ImageIn", "ImagePatch", "ProductImportRow"):
        assert schemas[schema_name].get("example")

    public_variant = schemas["VariantPublicOut"]["properties"]
    seller_variant = schemas["VariantSellerOut"]["properties"]
    assert "cost" not in public_variant
    assert "margin" not in public_variant
    assert "cost" in seller_variant
    assert "margin" in seller_variant
