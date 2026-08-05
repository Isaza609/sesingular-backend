from io import BytesIO

from app.models import Category, Store, StoreMember, User, Warehouse
from app.models.user import UserRole


def _seller_store(db):
    seller = User(id="seller-prod-03", email="seller-prod-03@example.com", name="Seller PROD", role=UserRole.seller)
    store = Store(id="store-prod-03", slug="store-prod-03", name="Tienda PROD", social_links={})
    warehouse = Warehouse(id="warehouse-prod-03", store_id=store.id, name="Bodega", active=True, is_default=True)
    category = Category(id="category-prod-03", store_id=store.id, slug="camisas", name="Camisas", active=True)
    db.add_all([seller, store, warehouse, category])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller


def test_hu_prod_03_download_template(api_context):
    client, db, _auth, token_for = api_context
    seller = _seller_store(db)

    response = client.get("/api/v1/seller/products/import/template", headers=token_for(seller.id))

    assert response.status_code == 200
    assert "name,slug,description" in response.text
    assert "CAM-NEG-S" in response.text


def test_hu_prod_03_import_csv_with_row_errors(api_context):
    client, db, _auth, token_for = api_context
    seller = _seller_store(db)
    csv_data = (
        "name,slug,description,short_desc,category_slug,sku,price,cost,stock,status,image_url\n"
        "Camisa negra,camisa-negra,Desc,Corta,camisas,CAM-NEG-S,70000,30000,12,active,https://cdn.example.com/camisa.jpg\n"
        "Producto malo,producto-malo,Desc,Corta,camisas,CAM-MAL,abc,100,1,active,\n"
    )

    response = client.post(
        "/api/v1/seller/products/import",
        headers=token_for(seller.id),
        files={"file": ("productos.csv", BytesIO(csv_data.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created_count"] == 1
    assert body["error_count"] == 1
    assert body["items"][0]["slug"] == "camisa-negra"
    assert body["errors"][0]["row"] == 3


def test_hu_prod_03_rejects_missing_required_columns(api_context):
    client, db, _auth, token_for = api_context
    seller = _seller_store(db)

    response = client.post(
        "/api/v1/seller/products/import",
        headers=token_for(seller.id),
        files={"file": ("productos.csv", BytesIO(b"name,sku\nCamisa,CAM-1\n"), "text/csv")},
    )

    assert response.status_code == 400
    assert "price" in response.json()["detail"]
