from tests.checkout_test_utils import add_cart_item, seed_checkout_store


def test_hu_chk_04_checkout_returns_summary_and_sends_email(api_context, monkeypatch):
    client, db, _auth, token_for = api_context
    sent = []

    def fake_summary(to, confirmation):
        sent.append((to, confirmation))

    monkeypatch.setattr("app.modules.common.mailer.checkout_summary_to_buyer", fake_summary)
    shipping = {"shipping_mode": "to_agree", "shipping_flat_cost": 0, "shipping_free_threshold": 0, "shipping_zones": []}
    _seller, buyer, _store, _product, variant, address, cart, _warehouses = seed_checkout_store(db, "04", price=45000, shipping_config=shipping)
    add_cart_item(db, cart, variant, 1)

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card", "notes": "Entregar en porteria"},
    )

    assert checkout.status_code == 201
    body = checkout.json()
    assert body["purchase_id"]
    assert body["summary"]["address"]["id"] == address.id
    assert body["summary"]["payment_method"] == "card"
    assert body["summary"]["store_quotes"][0]["items"][0]["quantity"] == 1
    assert body["summary"]["store_quotes"][0]["shipping"]["to_agree"] is True
    assert body["shipping_notes"]
    assert sent and sent[0][0] == buyer.email
    assert sent[0][1]["purchase_id"] == body["purchase_id"]
