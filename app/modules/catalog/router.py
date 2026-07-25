from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Category, InventoryMovement, PayoutAccount, PlatformSetting, Product, ProductCategory, ProductImage, ProductVariant, StockLevel, Store, Warehouse
from app.models.catalog import ProductStatus
from app.models.inventory import InventoryReason
from app.models.user import User
from app.modules.catalog.schemas import (
    CategoryIn,
    CategoryOut,
    CategoryPatch,
    ImageIn,
    ProductIn,
    ProductListOut,
    ProductOut,
    ProductPatch,
    StoreListPublicOut,
    StorePublicOut,
    VariantIn,
    VariantPatch,
    ProductImportRow,
    StoreSettingsIn,
)
from app.modules.common.permissions import ensure_store_member, get_seller_store, require_seller
from app.modules.auth.deps import get_current_user

public_router = APIRouter(prefix="/catalog", tags=["catalog"])
seller_router = APIRouter(prefix="/seller", tags=["seller-catalog"])


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower().strip())
    return value.strip("-") or str(uuid.uuid4())[:8]


def _stock(variant: ProductVariant) -> int:
    return sum(max(0, level.quantity - level.reserved) for level in variant.stock_levels)


def _product_out(product: Product) -> dict:
    variants = [
        {
            "id": variant.id,
            "sku": variant.sku,
            "name": variant.name,
            "color": variant.color,
            "size": variant.size,
            "price": variant.price,
            "compare_at": variant.compare_at,
            "cost": variant.cost,
            "active": variant.active,
            "stock": _stock(variant),
        }
        for variant in sorted(product.variants, key=lambda item: item.sku)
        if variant.active
    ]
    total_stock = sum(item["stock"] for item in variants)
    first = variants[0] if variants else {"price": 0, "compare_at": None}
    return {
        "id": product.id,
        "store_id": product.store_id,
        "store_name": product.store.name,
        "slug": product.slug,
        "name": product.name,
        "short_desc": product.short_desc,
        "description": product.description,
        "material": product.material,
        "badge": product.badge,
        "bestseller": product.bestseller,
        "status": product.status.value,
        "categories": [
            {"id": link.category.id, "slug": link.category.slug, "name": link.category.name}
            for link in product.category_links
            if link.category.active
        ],
        "variants": variants,
        "images": [
            {"id": image.id, "url": image.url, "alt": image.alt, "sort_order": image.sort_order}
            for image in sorted(product.images, key=lambda item: item.sort_order)
        ],
        "stock": total_stock,
        "price": first["price"],
        "compare_at": first["compare_at"],
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


def _category_out(category: Category) -> CategoryOut:
    return CategoryOut(
        id=category.id,
        store_id=category.store_id,
        parent_id=category.parent_id,
        slug=category.slug,
        name=category.name,
        sort_order=category.sort_order,
        active=category.active,
    )


def _product_query(store_id: str | None = None):
    stmt = select(Product).join(Store).where(Store.active.is_(True))
    if store_id:
        stmt = stmt.where(Product.store_id == store_id)
    return stmt


@public_router.get("/stores", response_model=StoreListPublicOut)
def public_stores(db: Session = Depends(get_db)):
    stores = db.scalars(select(Store).where(Store.active.is_(True)).order_by(Store.name)).all()
    return {"items": [StorePublicOut.model_validate(store, from_attributes=True) for store in stores]}


@public_router.get("/stores/{store_id}/payment-options")
def public_store_payment_options(store_id: str, db: Session = Depends(get_db)):
    """Métodos habilitados por el vendedor y sus cuentas de cobro activas (RF-PAGO-02)."""
    store = db.get(Store, store_id)
    if store is None or not store.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tienda no encontrada")
    row = db.get(PlatformSetting, f"store_config:{store_id}")
    config = row.value if row else StoreSettingsIn().model_dump()
    accounts = db.scalars(
        select(PayoutAccount)
        .where(PayoutAccount.store_id == store_id, PayoutAccount.active.is_(True))
        .order_by(PayoutAccount.created_at)
    ).all()
    return {
        "store_id": store_id,
        "store_name": store.name,
        "payment_methods": config.get("payment_methods", []),
        "payout_accounts": [
            {
                "id": account.id,
                "type": account.type.value,
                "label": account.label,
                "bank_name": account.bank_name,
                "account_type": account.account_type,
                "account_number": account.account_number,
                "breb_key": account.breb_key,
                "holder_name": account.holder_name,
                "holder_document": account.holder_document,
            }
            for account in accounts
        ],
    }


@public_router.get("/categories", response_model=list[CategoryOut])
def public_categories(store_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Category).where(Category.active.is_(True)).order_by(Category.sort_order, Category.name)
    if store_id:
        stmt = stmt.where(Category.store_id == store_id)
    return [_category_out(category) for category in db.scalars(stmt).all()]


@public_router.get("/products", response_model=ProductListOut)
def public_products(
    q: str | None = None,
    category: str | None = None,
    store_id: str | None = None,
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    in_stock: bool = False,
    sort: str = Query("destacados", pattern="^(destacados|nuevos|precio-asc|precio-desc|vendidos)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = _product_query(store_id).where(Product.status == ProductStatus.active)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Product.name).like(pattern), func.lower(Product.short_desc).like(pattern))
        )
    if category:
        stmt = stmt.join(ProductCategory).join(Category).where(
            Category.slug == category, Category.active.is_(True)
        )
    price = select(func.min(ProductVariant.price)).where(ProductVariant.product_id == Product.id).scalar_subquery()
    if min_price is not None:
        stmt = stmt.where(price >= min_price)
    if max_price is not None:
        stmt = stmt.where(price <= max_price)
    if in_stock:
        stmt = stmt.where(Product.variants.any(ProductVariant.stock_levels.any(StockLevel.quantity > StockLevel.reserved)))
    if sort == "nuevos":
        stmt = stmt.order_by(Product.created_at.desc())
    elif sort == "precio-asc":
        stmt = stmt.order_by(price.asc())
    elif sort == "precio-desc":
        stmt = stmt.order_by(price.desc())
    elif sort == "vendidos":
        stmt = stmt.order_by(Product.bestseller.desc(), Product.created_at.desc())
    else:  # destacados
        stmt = stmt.order_by(Product.bestseller.desc(), Product.created_at.desc())
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return ProductListOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProductOut.model_validate(_product_out(row)) for row in rows],
    )


def _find_public_product(slug: str, store_id: str | None, db: Session) -> Product:
    stmt = _product_query(store_id).where(Product.slug == slug, Product.status == ProductStatus.active)
    product = db.scalars(stmt.order_by(Product.created_at.desc())).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return product


@public_router.get("/products/{slug}", response_model=ProductOut)
def public_product(slug: str, store_id: str | None = None, db: Session = Depends(get_db)):
    return ProductOut.model_validate(_product_out(_find_public_product(slug, store_id, db)))


@seller_router.get("/store")
def seller_store(store: Store = Depends(get_seller_store)):
    return {
        "id": store.id,
        "slug": store.slug,
        "name": store.name,
        "description": store.description,
        "logo_url": store.logo_url,
        "contact_email": store.contact_email,
        "contact_phone": store.contact_phone,
        "active": store.active,
    }


@seller_router.patch("/store")
def patch_seller_store(body: dict, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    allowed = {"name", "description", "logo_url", "contact_email", "contact_phone"}
    for key, value in body.items():
        if key in allowed:
            setattr(store, key, value)
    db.commit()
    db.refresh(store)
    return seller_store(store)


@seller_router.get("/store/settings")
def seller_store_settings(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    row = db.get(PlatformSetting, f"store_config:{store.id}")
    return row.value if row else StoreSettingsIn().model_dump()


@seller_router.put("/store/settings")
def update_seller_store_settings(
    body: StoreSettingsIn,
    store: Store = Depends(get_seller_store),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    key = f"store_config:{store.id}"
    row = db.get(PlatformSetting, key)
    if row is None:
        row = PlatformSetting(key=key, value=body.model_dump(), updated_by=user.id)
        db.add(row)
    else:
        row.value = body.model_dump()
        row.updated_by = user.id
    db.commit()
    db.refresh(row)
    return row.value


@seller_router.get("/categories", response_model=list[CategoryOut])
def seller_categories(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).where(Category.store_id == store.id).order_by(Category.sort_order, Category.name)).all()
    return [_category_out(row) for row in rows]


@seller_router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    if body.parent_id:
        parent = db.get(Category, body.parent_id)
        if parent is None or parent.store_id != store.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoría padre no pertenece a tu tienda")
    category = Category(
        store_id=store.id,
        slug=_slug(body.slug or body.name),
        name=body.name,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
        active=body.active,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return _category_out(category)


@seller_router.patch("/categories/{category_id}", response_model=CategoryOut)
def patch_category(category_id: str, body: CategoryPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None or category.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    values = body.model_dump(exclude_unset=True)
    if values.get("parent_id"):
        parent = db.get(Category, values["parent_id"])
        if parent is None or parent.store_id != store.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoría padre no pertenece a tu tienda")
    if "slug" in values and values["slug"]:
        values["slug"] = _slug(values["slug"])
    for key, value in values.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return _category_out(category)


@seller_router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None or category.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    category.active = False
    db.commit()


@seller_router.get("/products", response_model=ProductListOut)
def seller_products(
    status_filter: str | None = Query(None, alias="status", pattern="^(draft|active|out_of_stock|discontinued)$"),
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = select(Product).where(Product.store_id == store.id)
    if status_filter:
        stmt = stmt.where(Product.status == status_filter)
    if q:
        stmt = stmt.where(func.lower(Product.name).like(f"%{q.lower()}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return ProductListOut(total=total, page=page, page_size=page_size, items=[ProductOut.model_validate(_product_out(row)) for row in rows])


def _seller_product(product_id: str, store: Store, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return product


@seller_router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(body: ProductIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = Product(
        store_id=store.id,
        slug=_slug(body.slug or body.name),
        name=body.name,
        short_desc=body.short_desc,
        description=body.description,
        material=body.material,
        badge=body.badge,
        bestseller=body.bestseller,
        status=body.status,
    )
    db.add(product)
    db.flush()
    _replace_categories(product, body.category_ids, store.id, db)
    for variant_data in body.variants:
        db.add(ProductVariant(product_id=product.id, **variant_data.model_dump()))
    for image_data in body.images:
        db.add(ProductImage(product_id=product.id, **image_data.model_dump()))
    db.commit()
    db.refresh(product)
    return ProductOut.model_validate(_product_out(product))


def _replace_categories(product: Product, ids: list[str], store_id: str, db: Session) -> None:
    categories = db.scalars(select(Category).where(Category.id.in_(ids), Category.store_id == store_id)).all() if ids else []
    if len(categories) != len(set(ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Una categoría no pertenece a tu tienda")
    product.category_links.clear()
    for category in categories:
        product.category_links.append(ProductCategory(product_id=product.id, category_id=category.id))


@seller_router.patch("/products/{product_id}", response_model=ProductOut)
def patch_product(product_id: str, body: ProductPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    values = body.model_dump(exclude_unset=True)
    category_ids = values.pop("category_ids", None)
    if "slug" in values and values["slug"]:
        values["slug"] = _slug(values["slug"])
    if "status" in values:
        values["status"] = ProductStatus(values["status"])
    for key, value in values.items():
        setattr(product, key, value)
    if category_ids is not None:
        _replace_categories(product, category_ids, store.id, db)
    db.commit()
    db.refresh(product)
    return ProductOut.model_validate(_product_out(product))


@seller_router.delete("/products/{product_id}", response_model=ProductOut)
def discontinue_product(product_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    product.status = ProductStatus.discontinued
    db.commit()
    db.refresh(product)
    return ProductOut.model_validate(_product_out(product))


@seller_router.post("/products/{product_id}/variants", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_variant(product_id: str, body: VariantIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    variant = ProductVariant(product_id=product.id, **body.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return {"id": variant.id, **body.model_dump(), "stock": 0}


@seller_router.patch("/variants/{variant_id}", response_model=dict)
def patch_variant(variant_id: str, body: VariantPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    variant = db.get(ProductVariant, variant_id)
    if variant is None or variant.product.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no encontrada")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(variant, key, value)
    db.commit()
    db.refresh(variant)
    return {"id": variant.id, "sku": variant.sku, "name": variant.name, "color": variant.color, "size": variant.size, "price": variant.price, "compare_at": variant.compare_at, "cost": variant.cost, "active": variant.active, "stock": _stock(variant)}


@seller_router.post("/products/{product_id}/images", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_image(product_id: str, body: ImageIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    image = ProductImage(product_id=product.id, **body.model_dump())
    db.add(image)
    db.commit()
    db.refresh(image)
    return {"id": image.id, **body.model_dump()}


@seller_router.post("/products/import", response_model=list[ProductOut], status_code=status.HTTP_201_CREATED)
def import_products(rows: list[ProductImportRow], store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    """Importa filas ya normalizadas por el cliente desde CSV/XLSX."""
    warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True), Warehouse.is_default.is_(True)))
    if warehouse is None:
        warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True)).order_by(Warehouse.name))
    if warehouse is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes registrar un almacén antes de importar inventario")
    created = []
    for row in rows:
        product = Product(store_id=store.id, slug=_slug(row.name), name=row.name, status=ProductStatus.draft)
        db.add(product)
        db.flush()
        variant = ProductVariant(product_id=product.id, sku=row.sku, price=row.price, cost=row.cost)
        db.add(variant)
        db.flush()
        db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=row.stock))
        db.add(InventoryMovement(variant_id=variant.id, warehouse_id=warehouse.id, delta=row.stock, reason=InventoryReason.restock, note="Importación masiva"))
        created.append(product)
    db.commit()
    for product in created:
        db.refresh(product)
    return [ProductOut.model_validate(_product_out(product)) for product in created]
