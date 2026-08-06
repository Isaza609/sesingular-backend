from app.main import app


HU_BY_OPERATION = {
    ("/api/v1/checkout", "post"): "HU-CANAL-01",
    ("/api/v1/seller/pos/orders", "post"): "HU-CANAL-02",
    ("/api/v1/seller/reports/sales", "get"): "HU-CANAL-03",
}

PRIVATE_PATHS = [
    "/api/v1/checkout",
    "/api/v1/seller/pos/orders",
    "/api/v1/seller/reports/sales",
]


def test_canal_routes_include_hu_traceability_and_response_contract():
    paths = app.openapi()["paths"]
    for (path, method), hu in HU_BY_OPERATION.items():
        operation = paths[path][method]
        assert hu in operation["description"]
        assert operation.get("summary")
        assert operation.get("responses")
        assert "200" in operation["responses"] or "201" in operation["responses"]


def test_canal_private_routes_require_bearer_authentication():
    paths = app.openapi()["paths"]
    for path in PRIVATE_PATHS:
        for operation in paths[path].values():
            assert any("HTTPBearer" in security for security in operation.get("security", []))


def test_canal_openapi_schemas_expose_channel_pos_and_report_contracts():
    schemas = app.openapi()["components"]["schemas"]
    order_props = schemas["OrderOut"]["properties"]
    pos_props = schemas["PosOrderIn"]["properties"]
    report_props = schemas["SalesChannelReportOut"]["properties"]

    assert order_props["channel"]["pattern"] == "^(online|presencial)$"
    assert "description" in order_props["channel"]
    assert pos_props["items"]["minItems"] == 1
    assert "example" in schemas["PosOrderIn"]
    assert set(report_props) == {"totals", "by_channel"}
    assert "example" in schemas["SalesChannelReportOut"]
