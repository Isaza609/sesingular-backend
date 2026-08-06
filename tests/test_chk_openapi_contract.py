def test_chk_openapi_contract_documents_cart_checkout_and_purchases(api_context):
    client, _db, _auth, _token_for = api_context
    spec = client.get("/api/v1/openapi.json")
    if spec.status_code == 404:
        spec = client.get("/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]

    cart_get = paths["/api/v1/cart"]["get"]
    cart_post = paths["/api/v1/cart/items"]["post"]
    quote = paths["/api/v1/checkout/quote"]["post"]
    checkout = paths["/api/v1/checkout"]["post"]
    purchases = paths["/api/v1/purchases"]["get"]
    purchase_detail = paths["/api/v1/purchases/{purchase_id}"]["get"]

    assert "HU-CHK-01" in cart_get["description"]
    assert "HU-CHK-01" in cart_post["description"]
    assert "HU-CHK-02" in quote["description"]
    assert "HU-CHK-03" in checkout["description"]
    assert "HU-CHK-04" in checkout["description"]
    assert "HU-CHK-05" in checkout["description"]
    assert "HU-CHK-05" in purchases["description"]
    assert "HU-CHK-05" in purchase_detail["description"]
    for operation in [cart_get, cart_post, quote, checkout, purchases, purchase_detail]:
        assert operation["summary"]
        assert operation["responses"]
    assert "CheckoutQuoteIn" in spec.json()["components"]["schemas"]
    assert "CheckoutConfirmationOut" in spec.json()["components"]["schemas"]
    assert "PurchaseOut" in spec.json()["components"]["schemas"]
    assert quote["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("CheckoutQuoteIn")
    assert checkout["responses"]["201"]["content"]["application/json"]["schema"]["$ref"].endswith("CheckoutConfirmationOut")
