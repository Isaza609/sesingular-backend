from app.main import app


def test_role_contract_routes_are_registered():
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/admin/users",
        "/api/v1/admin/stores",
        "/api/v1/catalog/products",
        "/api/v1/cart",
        "/api/v1/checkout",
        "/api/v1/orders",
        "/api/v1/seller/products",
        "/api/v1/seller/inventory",
        "/api/v1/seller/pos/orders",
        "/api/v1/seller/orders",
        "/api/v1/payments/webhooks/{provider}",
    }
    assert expected <= paths.keys()


def test_private_role_routers_require_bearer_authentication():
    paths = app.openapi()["paths"]
    for path in ("/api/v1/admin/users", "/api/v1/cart", "/api/v1/seller/products"):
        operations = paths[path].values()
        assert any("HTTPBearer" in security for operation in operations for security in operation.get("security", []))

