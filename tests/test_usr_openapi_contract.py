from app.main import app


USR_ENDPOINTS = {
    ("/api/v1/auth/register", "post"): "HU-USR-01",
    ("/api/v1/auth/login", "post"): "HU-USR-01",
    ("/api/v1/auth/change-password", "post"): "HU-USR-02",
    ("/api/v1/auth/me", "get"): "HU-USR-03",
    ("/api/v1/auth/me", "patch"): "HU-USR-03",
    ("/api/v1/addresses", "get"): "HU-USR-03",
    ("/api/v1/addresses", "post"): "HU-USR-03",
    ("/api/v1/addresses/{address_id}", "patch"): "HU-USR-03",
    ("/api/v1/addresses/{address_id}", "delete"): "HU-USR-03",
    ("/api/v1/auth/password-recovery/request", "post"): "HU-USR-04",
    ("/api/v1/auth/password-recovery/confirm", "post"): "HU-USR-04",
    ("/api/v1/admin/stores/{store_id}/members", "get"): "HU-USR-05",
    ("/api/v1/admin/stores/{store_id}/members", "post"): "HU-USR-05",
    ("/api/v1/admin/stores/{store_id}/members/{user_id}", "patch"): "HU-USR-05",
    ("/api/v1/seller/store/members", "get"): "HU-USR-05",
}


def test_usr_epic_routes_are_registered_and_documented():
    spec = app.openapi()
    for (path, method), hu in USR_ENDPOINTS.items():
        assert path in spec["paths"], path
        operation = spec["paths"][path][method]
        assert operation.get("summary"), (path, method)
        assert hu in operation.get("description", ""), (path, method)
        success_codes = [code for code in operation["responses"] if code.startswith("2")]
        assert success_codes, (path, method)
        assert operation["responses"][success_codes[0]]["description"]
        assert any(code in operation["responses"] for code in ("400", "401", "403", "404", "409", "422", "502"))


def test_private_usr_routes_require_bearer_authentication():
    spec = app.openapi()
    private_paths = [
        "/api/v1/auth/me",
        "/api/v1/auth/change-password",
        "/api/v1/addresses",
        "/api/v1/admin/stores/{store_id}/members",
        "/api/v1/seller/store/members",
    ]
    for path in private_paths:
        for operation in spec["paths"][path].values():
            assert any("HTTPBearer" in security for security in operation.get("security", [])), path
