from app.models import Product, ProductVariant, Store, StoreMember, User
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def _seller_product(db):
    seller = User(id="seller-prod-04", email="seller-prod-04@example.com", name="Seller PROD", role=UserRole.seller)
    store = Store(id="store-prod-04", slug="store-prod-04", name="Tienda PROD", social_links={})
    product = Product(id="product-prod-04", store_id=store.id, slug="zapato", name="Zapato", status=ProductStatus.active)
    variant = ProductVariant(id="variant-prod-04", product_id=product.id, sku="ZAP-NEG", color="Negro", price=120000)
    other_product = Product(id="product-prod-04-other", store_id=store.id, slug="bolso", name="Bolso", status=ProductStatus.active)
    other_variant = ProductVariant(id="variant-prod-04-other", product_id=other_product.id, sku="BOL-NEG", price=90000)
    db.add_all([seller, store, product, variant, other_product, other_variant])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store, product, variant, other_variant


def test_hu_prod_04_product_and_variant_images_are_public(api_context):
    client, db, _auth, token_for = api_context
    seller, store, product, variant, _other_variant = _seller_product(db)

    general = client.post(
        f"/api/v1/seller/products/{product.id}/images",
        headers=token_for(seller.id),
        json={"url": "https://cdn.example.com/zapato-frente.jpg", "alt": "Frente", "sort_order": 1},
    )
    specific = client.post(
        f"/api/v1/seller/products/{product.id}/images",
        headers=token_for(seller.id),
        json={"url": "https://cdn.example.com/zapato-negro.jpg", "alt": "Negro", "sort_order": 2, "variant_id": variant.id},
    )
    public = client.get("/api/v1/catalog/products/zapato", params={"store_id": store.id})

    assert general.status_code == 201
    assert specific.status_code == 201
    assert public.json()["images"][0]["url"].endswith("zapato-frente.jpg")
    variant_images = public.json()["variants"][0]["images"]
    assert variant_images[0]["variant_id"] == variant.id


def test_hu_prod_04_rejects_foreign_variant_and_deletes_image(api_context):
    client, db, _auth, token_for = api_context
    seller, store, product, _variant, other_variant = _seller_product(db)
    image = client.post(
        f"/api/v1/seller/products/{product.id}/images",
        headers=token_for(seller.id),
        json={"url": "https://cdn.example.com/zapato.jpg"},
    ).json()

    invalid = client.patch(
        f"/api/v1/seller/products/{product.id}/images/{image['id']}",
        headers=token_for(seller.id),
        json={"variant_id": other_variant.id},
    )
    deleted = client.delete(f"/api/v1/seller/products/{product.id}/images/{image['id']}", headers=token_for(seller.id))
    public = client.get("/api/v1/catalog/products/zapato", params={"store_id": store.id})

    assert invalid.status_code == 400
    assert deleted.status_code == 204
    assert public.json()["images"] == []
