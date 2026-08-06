from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/catalog/products", "get"): ("HU-BUS-01", "HU-BUS-02"),
    ("/api/v1/catalog/products/{slug}", "get"): ("HU-BUS-03",),
}


def test_bus_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hus in HU_BY_OPERATION.items():
        operation = paths[path][method]
        for hu in hus:
            assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert "200" in operation["responses"]


def test_bus_public_routes_do_not_require_bearer_authentication():
    paths = app.openapi()["paths"]
    for path in HU_BY_OPERATION:
        operation = paths[path[0]][path[1]]
        assert not any("HTTPBearer" in security for security in operation.get("security", []))


def test_bus_openapi_parameters_and_schemas_are_documented():
    openapi = app.openapi()
    list_operation = openapi["paths"]["/api/v1/catalog/products"]["get"]
    params = {param["name"]: param for param in list_operation["parameters"]}
    schemas = openapi["components"]["schemas"]

    for name in ("q", "category", "store_id", "min_price", "max_price", "in_stock", "sort", "page", "page_size"):
        assert params[name]["description"]
    assert params["sort"]["schema"]["pattern"] == "^(relevancia|destacados|nuevos|precio-asc|precio-desc|vendidos)$"
    assert schemas["ProductListOut"]["properties"]["items"].get("description")
    assert schemas["ProductOut"]["properties"]["variants"].get("description")
    assert "store_contact" in schemas["ProductOut"]["properties"]
    assert "shipping" in schemas["ProductOut"]["properties"]
    assert schemas["VariantPublicOut"]["properties"]["available"].get("description")
