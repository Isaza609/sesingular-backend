from __future__ import annotations

import csv
import io
import re
import uuid
import zipfile
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.session import get_db
from app.models import Category, InventoryMovement, Order, OrderItem, PayoutAccount, PlatformSetting, Product, ProductCategory, ProductImage, ProductVariant, StockLevel, Store, Warehouse
from app.models.catalog import ProductStatus
from app.models.inventory import InventoryReason
from app.models.order import OrderStatus
from app.models.payout import PayoutAccountType
from app.models.user import User
from app.modules.catalog.schemas import (
    CategoryIn,
    CategoryOut,
    CategoryPatch,
    ImageIn,
    ImagePatch,
    ProductIn,
    ProductImportErrorOut,
    ProductListOut,
    ProductOut,
    ProductImportResultOut,
    ProductPatch,
    ProductSellerListOut,
    ProductSellerOut,
    StoreListPublicOut,
    StorePaymentOptionsOut,
    StorePublicOut,
    SellerStoreOut,
    SellerStorePatch,
    VariantSellerOut,
    VariantIn,
    VariantPatch,
    ProductImageOut,
    ProductImportRow,
    StoreSettingsIn,
    StoreSettingsOut,
)
from app.modules.common.permissions import ensure_store_member, get_seller_store, require_seller
from app.modules.auth.deps import get_current_user
from app.modules.inventory.service import available_for_variant
from app.modules.pricing.service import effective_unit_price, validate_special_price

public_router = APIRouter(prefix="/catalog", tags=["catalog"])
seller_router = APIRouter(prefix="/seller", tags=["seller-catalog"])
GATEWAY_METHODS = ("card", "pse", "nequi")
PROTECTED_STORE_FIELDS = {"name", "slug", "active", "legal_name", "tax_id", "fiscal_data", "delete"}
SELLER_STORE_RESPONSES = {
    400: {"description": "Campo administrado o regla de negocio no permitida."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "El vendedor no tiene una tienda activa."},
    422: {"description": "Validacion Pydantic."},
}
STORE_SETTINGS_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "El vendedor no tiene una tienda activa."},
    422: {"description": "Validacion Pydantic."},
}
CATEGORY_PUBLIC_RESPONSES = {
    422: {"description": "Validacion Pydantic."},
}
CATEGORY_SELLER_RESPONSES = {
    400: {"description": "Categoria padre invalida, jerarquia ciclica o regla de negocio no permitida."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "Categoria o tienda no encontrada."},
    409: {"description": "Ya existe una categoria con el mismo slug en la tienda."},
    422: {"description": "Validacion Pydantic."},
}
PRODUCT_CATEGORY_RESPONSES = {
    400: {"description": "Categorias duplicadas, inactivas o fuera de la tienda."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "Producto o tienda no encontrado."},
    409: {"description": "Conflicto de unicidad en slug o categoria."},
    422: {"description": "Validacion Pydantic."},
}
PRODUCT_SELLER_RESPONSES = {
    400: {"description": "Datos invalidos, estado no permitido o recurso asociado fuera de scope."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "Producto, variante, imagen o tienda no encontrada."},
    409: {"description": "Slug de producto o SKU de variante duplicado."},
    422: {"description": "Validacion Pydantic."},
}
PRODUCT_PUBLIC_RESPONSES = {
    404: {"description": "Producto no encontrado o no visible publicamente."},
    422: {"description": "Validacion Pydantic."},
}


def _store_public_out(store: Store) -> dict:
    return {
        "id": store.id,
        "slug": store.slug,
        "name": store.name,
        "description": store.description,
        "logo_url": store.logo_url,
        "contact_email": store.contact_email,
        "contact_phone": store.contact_phone,
        "whatsapp_phone": store.whatsapp_phone,
        "social_links": store.social_links or {},
    }


def _seller_store_out(store: Store) -> dict:
    return {**_store_public_out(store), "active": store.active}


def get_store_settings_value(store_id: str, db: Session) -> StoreSettingsOut:
    row = db.get(PlatformSetting, f"store_config:{store_id}")
    return StoreSettingsOut.model_validate(row.value if row else {})


def _gateway_configured(db: Session) -> bool:
    row = db.get(PlatformSetting, "payment_gateway")
    value = row.value if row else {}
    return bool(value.get("provider"))


def payment_options_for_store(store_id: str, db: Session) -> dict:
    store = db.get(Store, store_id)
    if store is None or not store.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tienda no encontrada")

    settings = get_store_settings_value(store_id, db)
    methods: list[str] = []
    account_types: set[PayoutAccountType] = set()
    if settings.payment_methods.gateway_enabled and _gateway_configured(db):
        methods.extend(GATEWAY_METHODS)
    if settings.payment_methods.manual_transfer_enabled:
        account_types.add(PayoutAccountType.bank)
    if settings.payment_methods.manual_breb_enabled:
        account_types.add(PayoutAccountType.bre_b)

    accounts = db.scalars(
        select(PayoutAccount)
        .where(PayoutAccount.store_id == store_id, PayoutAccount.active.is_(True))
        .order_by(PayoutAccount.created_at)
    ).all()
    filtered_accounts = [account for account in accounts if account.type in account_types]
    if any(account.type == PayoutAccountType.bank for account in filtered_accounts):
        methods.append("transfer")
    if any(account.type == PayoutAccountType.bre_b for account in filtered_accounts):
        methods.append("breb")

    return {
        "store_id": store_id,
        "store_name": store.name,
        "payment_methods": methods,
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
            for account in filtered_accounts
        ],
    }


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower().strip())
    return value.strip("-") or str(uuid.uuid4())[:8]


def _stock(variant: ProductVariant) -> int:
    return available_for_variant(variant)


def _image_out(image: ProductImage) -> dict:
    return {
        "id": image.id,
        "url": image.url,
        "alt": image.alt,
        "sort_order": image.sort_order,
        "variant_id": image.variant_id,
    }


def _variant_out(variant: ProductVariant, *, include_internal: bool = False, product_status: ProductStatus | None = None) -> dict:
    stock = _stock(variant)
    visible_active = variant.active
    available = visible_active and stock > 0 and product_status == ProductStatus.active
    pricing = effective_unit_price(variant)
    data = {
        "id": variant.id,
        "sku": variant.sku,
        "name": variant.name,
        "color": variant.color,
        "size": variant.size,
        "price": pricing["price"],
        "regular_price": pricing["regular_price"],
        "compare_at": variant.compare_at,
        "special_price": variant.special_price,
        "special_starts_at": variant.special_starts_at,
        "special_ends_at": variant.special_ends_at,
        "special_price_active": pricing["special_price_active"],
        "active": variant.active,
        "stock": stock,
        "available": available,
        "images": [_image_out(image) for image in sorted(variant.images, key=lambda item: item.sort_order)],
    }
    if include_internal:
        margin = pricing["price"] - variant.cost if variant.cost is not None else None
        data.update(
            {
                "cost": variant.cost,
                "margin": margin,
                "margin_pct": round((margin / pricing["price"]) * 100, 2) if margin is not None and pricing["price"] else None,
                "margin_missing_cost": variant.cost is None,
            }
        )
    return data


def _product_out(product: Product, *, include_internal: bool = False, include_store_context: bool = False, db: Session | None = None) -> dict:
    variants = [
        _variant_out(variant, include_internal=include_internal, product_status=product.status)
        for variant in sorted(product.variants, key=lambda item: item.sku)
        if variant.active
    ]
    total_stock = sum(item["stock"] for item in variants)
    first = min(variants, key=lambda item: item["price"]) if variants else {"price": 0, "compare_at": None}
    data = {
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
            _image_out(image)
            for image in sorted(product.images, key=lambda item: item.sort_order)
            if image.variant_id is None
        ],
        "stock": total_stock,
        "price": first["price"],
        "compare_at": first["compare_at"],
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
    if include_store_context and db is not None:
        data["store_contact"] = _product_store_contact_out(product.store)
        data["shipping"] = _product_shipping_out(product.store_id, db)
    return data


def _seller_product_out(product: Product) -> dict:
    return _product_out(product, include_internal=True)


def _product_store_contact_out(store: Store) -> dict:
    return {
        "email": store.contact_email,
        "phone": store.contact_phone,
        "whatsapp_phone": store.whatsapp_phone,
    }


def _product_shipping_out(store_id: str, db: Session) -> dict:
    settings = get_store_settings_value(store_id, db)
    zones = settings.shipping_zones or []
    return {
        "flat_cost": settings.shipping_flat_cost,
        "free_threshold": settings.shipping_free_threshold,
        "zones": zones,
        "to_agree": settings.shipping_flat_cost == 0 and not zones,
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


def _validate_category_parent(
    parent_id: str | None,
    store_id: str,
    db: Session,
    *,
    category_id: str | None = None,
) -> None:
    if parent_id is None:
        return
    if category_id is not None and parent_id == category_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoria no puede ser padre de si misma")
    parent = db.get(Category, parent_id)
    if parent is None or parent.store_id != store_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoria padre no pertenece a tu tienda")
    current = parent
    while current is not None:
        if current.id == category_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La jerarquia de categorias no puede tener ciclos")
        current = db.get(Category, current.parent_id) if current.parent_id else None


def _ensure_unique_category_slug(store_id: str, slug: str, db: Session, *, exclude_id: str | None = None) -> None:
    stmt = select(Category).where(Category.store_id == store_id, Category.slug == slug)
    if exclude_id:
        stmt = stmt.where(Category.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoria con ese slug en tu tienda")


def _ensure_unique_product_slug(store_id: str, slug: str, db: Session, *, exclude_id: str | None = None) -> None:
    stmt = select(Product).where(Product.store_id == store_id, Product.slug == slug)
    if exclude_id:
        stmt = stmt.where(Product.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un producto con ese slug en tu tienda")


def _ensure_unique_variant_sku(product_id: str, sku: str, db: Session, *, exclude_id: str | None = None) -> None:
    stmt = select(ProductVariant).where(ProductVariant.product_id == product_id, ProductVariant.sku == sku)
    if exclude_id:
        stmt = stmt.where(ProductVariant.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una variante con ese SKU en el producto")


def _commit_product(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Conflicto de unicidad en producto o variante") from exc


def _seller_variant(variant_id: str, store: Store, db: Session) -> ProductVariant:
    variant = db.get(ProductVariant, variant_id)
    if variant is None or variant.product.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no encontrada")
    return variant


def _seller_image(product_id: str, image_id: str, store: Store, db: Session) -> ProductImage:
    product = _seller_product(product_id, store, db)
    image = db.get(ProductImage, image_id)
    if image is None or image.product_id != product.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagen no encontrada")
    return image


def _validate_image_variant(product: Product, variant_id: str | None, db: Session) -> None:
    if variant_id is None:
        return
    variant = db.get(ProductVariant, variant_id)
    if variant is None or variant.product_id != product.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La variante de la imagen no pertenece al producto")


def _commit_category(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoria con ese slug en tu tienda") from exc


def _product_query(store_id: str | None = None):
    stmt = select(Product).join(Store).where(Store.active.is_(True))
    if store_id:
        stmt = stmt.where(Product.store_id == store_id)
    return stmt


def _sold_units_by_product(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(ProductVariant.product_id, func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(OrderItem, OrderItem.variant_id == ProductVariant.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != OrderStatus.cancelled)
        .group_by(ProductVariant.product_id)
    ).all()
    return {product_id: int(quantity or 0) for product_id, quantity in rows}


@public_router.get(
    "/stores",
    response_model=StoreListPublicOut,
    status_code=status.HTTP_200_OK,
    summary="Listar tiendas",
    description="Endpoint publico. HU-TDA-01. Lista tiendas activas con informacion publica de contacto visible para compradores.",
    response_description="Tiendas activas con datos publicos actualizados.",
    responses={422: {"description": "Validacion Pydantic."}},
)
def public_stores(db: Session = Depends(get_db)):
    stores = db.scalars(select(Store).where(Store.active.is_(True)).order_by(Store.name)).all()
    return {"items": [StorePublicOut.model_validate(_store_public_out(store)) for store in stores]}


@public_router.get(
    "/stores/{store_id}/payment-options",
    response_model=StorePaymentOptionsOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar opciones de pago",
    description="Endpoint publico. HU-TDA-03. Muestra solo metodos de pago habilitados por la tienda y disponibles por cuentas activas/configuracion de pasarela.",
    response_description="Metodos y cuentas de cobro disponibles para checkout.",
    responses={
        404: {"description": "Tienda no encontrada o inactiva."},
        422: {"description": "Validacion Pydantic."},
    },
)
def public_store_payment_options(store_id: str, db: Session = Depends(get_db)):
    return payment_options_for_store(store_id, db)


@public_router.get(
    "/categories",
    response_model=list[CategoryOut],
    status_code=status.HTTP_200_OK,
    summary="Listar categorias publicas",
    description=(
        "Endpoint publico. HU-CAT-01. Lista categorias y subcategorias activas. "
        "Para navegar el catalogo de una tienda se debe enviar `store_id`; asi el comprador ve solo "
        "la jerarquia definida por esa tienda y no categorias de otras tiendas."
    ),
    response_description="Categorias activas con parent_id para reconstruir la jerarquia.",
    responses=CATEGORY_PUBLIC_RESPONSES,
)
def public_categories(store_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Category).where(Category.active.is_(True)).order_by(Category.sort_order, Category.name)
    if store_id:
        stmt = stmt.where(Category.store_id == store_id)
    return [_category_out(category) for category in db.scalars(stmt).all()]


@public_router.get(
    "/products",
    response_model=ProductListOut,
    status_code=status.HTTP_200_OK,
    summary="Buscar productos",
    description=(
        "Endpoint publico. HU-BUS-01, HU-BUS-02, HU-CAT-02, HU-PROD-01, HU-PROD-06 y HU-PROM-01. "
        "Busca productos visibles para compradores por nombre o descripcion, permite combinar filtros "
        "de tienda, categoria, precio efectivo y disponibilidad, y ordena por destacados, precio, nuevos "
        "o volumen real de ventas."
    ),
    response_description="Pagina de productos visibles filtrados y ordenados; puede retornar total cero sin error.",
    responses={400: {"description": "Rango de precio invalido."}, **PRODUCT_PUBLIC_RESPONSES},
)
def public_products(
    q: str | None = Query(default=None, description="Termino de busqueda sobre nombre, resumen o descripcion.", example="camisa"),
    category: str | None = Query(default=None, description="Slug de categoria activa por la que se filtra.", example="camisas"),
    store_id: str | None = Query(default=None, description="Identificador de tienda activa para acotar el catalogo.", example="store-nova"),
    min_price: int | None = Query(default=None, ge=0, description="Precio efectivo minimo en COP.", example=30000),
    max_price: int | None = Query(default=None, ge=0, description="Precio efectivo maximo en COP.", example=80000),
    in_stock: bool = Query(default=False, description="Cuando es true, retorna solo productos con disponibilidad real.", example=True),
    sort: str = Query("destacados", description="Orden: relevancia, destacados, nuevos, precio-asc, precio-desc o vendidos.", pattern="^(relevancia|destacados|nuevos|precio-asc|precio-desc|vendidos)$", example="precio-asc"),
    page: int = Query(1, ge=1, description="Pagina solicitada.", example=1),
    page_size: int = Query(24, ge=1, le=100, description="Cantidad de productos por pagina.", example=24),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "min_price no puede ser mayor que max_price")

    stmt = _product_query(store_id).where(Product.status.in_([ProductStatus.active, ProductStatus.out_of_stock]))
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(Product.short_desc).like(pattern),
                func.lower(Product.description).like(pattern),
            )
        )
    if category:
        stmt = stmt.join(ProductCategory).join(Category).where(
            Category.slug == category, Category.active.is_(True)
        )
    rows = db.scalars(stmt).unique().all()
    items = [ProductOut.model_validate(_product_out(row)) for row in rows]

    if min_price is not None:
        items = [item for item in items if item.price >= min_price]
    if max_price is not None:
        items = [item for item in items if item.price <= max_price]
    if in_stock:
        items = [item for item in items if item.stock > 0]

    if sort == "nuevos":
        items.sort(key=lambda item: (item.created_at, item.name), reverse=True)
    elif sort == "precio-asc":
        items.sort(key=lambda item: (item.price, item.name, item.id))
    elif sort == "precio-desc":
        items.sort(key=lambda item: (-item.price, item.name, item.id))
    elif sort == "vendidos":
        sold_units = _sold_units_by_product(db)
        items.sort(key=lambda item: (-sold_units.get(item.id, 0), not item.bestseller, item.name, item.id))
    else:
        term = (q or "").lower()
        items.sort(
            key=lambda item: (
                0 if term and term in item.name.lower() else 1,
                not item.bestseller,
                -item.created_at.timestamp(),
                item.name,
                item.id,
            )
        )

    total = len(items)
    page_items = items[(page - 1) * page_size : page * page_size]
    return ProductListOut(
        total=total,
        page=page,
        page_size=page_size,
        items=page_items,
    )


def _find_public_product(slug: str, store_id: str | None, db: Session) -> Product:
    stmt = _product_query(store_id).where(
        Product.slug == slug,
        Product.status.in_([ProductStatus.active, ProductStatus.out_of_stock]),
    )
    product = db.scalars(stmt.order_by(Product.created_at.desc())).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return product


@public_router.get(
    "/products/{slug}",
    response_model=ProductOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de producto",
    description=(
        "Endpoint publico. HU-BUS-03, HU-PROD-02, HU-PROD-04, HU-PROD-05, HU-PROD-06, HU-PROM-01 y HU-PROM-03. "
        "Retorna detalle publico del producto visible, variantes con precio efectivo, stock, disponibilidad, imagenes "
        "y datos de envio/contacto de la tienda, sin exponer costos internos."
    ),
    response_description="Detalle publico del producto con variantes, imagenes, disponibilidad y datos de envio/contacto.",
    responses=PRODUCT_PUBLIC_RESPONSES,
)
def public_product(
    slug: str,
    store_id: str | None = Query(default=None, description="Identificador de tienda activa para resolver slugs repetidos.", example="store-nova"),
    db: Session = Depends(get_db),
):
    return ProductOut.model_validate(_product_out(_find_public_product(slug, store_id, db), include_store_context=True, db=db))


@seller_router.get(
    "/store",
    response_model=SellerStoreOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar mi tienda",
    description="Rol permitido: seller. HU-TDA-01. Retorna la tienda asociada y separa datos publicos editables de campos administrados.",
    response_description="Perfil de tienda del vendedor autenticado.",
    responses=SELLER_STORE_RESPONSES,
)
def seller_store(store: Store = Depends(get_seller_store)):
    return _seller_store_out(store)


@seller_router.patch(
    "/store",
    response_model=SellerStoreOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar mi tienda",
    description="Rol permitido: seller. HU-TDA-01. Actualiza solo informacion publica; nombre, slug, estado y datos legales son gestion de administracion.",
    response_description="Perfil publico de tienda actualizado.",
    responses=SELLER_STORE_RESPONSES,
)
def patch_seller_store(body: SellerStorePatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    protected = PROTECTED_STORE_FIELDS & set(body.model_extra or {})
    if protected:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La administracion gestiona este dato de la tienda")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(store, key, value)
    db.commit()
    db.refresh(store)
    return _seller_store_out(store)


@seller_router.get(
    "/store/settings",
    response_model=StoreSettingsOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar configuracion de tienda",
    description="Rol permitido: seller. HU-TDA-03. Retorna metodos de pago aceptados y configuracion operativa de la tienda.",
    response_description="Configuracion vigente de la tienda.",
    responses=STORE_SETTINGS_RESPONSES,
)
def seller_store_settings(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    return get_store_settings_value(store.id, db)


@seller_router.put(
    "/store/settings",
    response_model=StoreSettingsOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar configuracion de tienda",
    description="Rol permitido: seller. HU-TDA-03. Define pasarela automatizada, transferencia bancaria y Bre-B aceptados por la tienda.",
    response_description="Configuracion actualizada de la tienda.",
    responses=STORE_SETTINGS_RESPONSES,
)
def update_seller_store_settings(
    body: StoreSettingsIn,
    store: Store = Depends(get_seller_store),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    key = f"store_config:{store.id}"
    value = body.model_dump(mode="json")
    row = db.get(PlatformSetting, key)
    if row is None:
        row = PlatformSetting(key=key, value=value, updated_by=user.id)
        db.add(row)
    else:
        row.value = value
        row.updated_by = user.id
    db.commit()
    db.refresh(row)
    return StoreSettingsOut.model_validate(row.value)


@seller_router.get(
    "/categories",
    response_model=list[CategoryOut],
    status_code=status.HTTP_200_OK,
    summary="Listar mis categorias",
    description=(
        "Rol permitido: seller. HU-CAT-01. Lista categorias y subcategorias propias de la tienda "
        "autenticada, incluidas inactivas, para administrar la jerarquia del catalogo."
    ),
    response_description="Categorias de la tienda autenticada con parent_id y estado.",
    responses=CATEGORY_SELLER_RESPONSES,
)
def seller_categories(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).where(Category.store_id == store.id).order_by(Category.sort_order, Category.name)).all()
    return [_category_out(row) for row in rows]


@seller_router.post(
    "/categories",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoria de mi tienda",
    description=(
        "Rol permitido: seller. HU-CAT-01. Crea una categoria raiz o subcategoria propia. "
        "`parent_id`, cuando se envia, debe pertenecer a la misma tienda; el slug es unico por tienda."
    ),
    response_description="Categoria creada y disponible para asignar productos de la tienda.",
    responses=CATEGORY_SELLER_RESPONSES,
)
def create_category(body: CategoryIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    slug = _slug(body.slug or body.name)
    _ensure_unique_category_slug(store.id, slug, db)
    if body.parent_id:
        parent = db.get(Category, body.parent_id)
        if parent is None or parent.store_id != store.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoría padre no pertenece a tu tienda")
    category = Category(
        store_id=store.id,
        slug=slug,
        name=body.name,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
        active=body.active,
    )
    db.add(category)
    _commit_category(db)
    db.refresh(category)
    return _category_out(category)


@seller_router.patch(
    "/categories/{category_id}",
    response_model=CategoryOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar categoria de mi tienda",
    description=(
        "Rol permitido: seller. HU-CAT-01. Actualiza nombre, slug, parent, orden o estado de una "
        "categoria propia. Rechaza parent de otra tienda, autociclos y ciclos de jerarquia."
    ),
    response_description="Categoria actualizada manteniendo el scope de la tienda.",
    responses=CATEGORY_SELLER_RESPONSES,
)
def patch_category(category_id: str, body: CategoryPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None or category.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    values = body.model_dump(exclude_unset=True)
    if "parent_id" in values:
        _validate_category_parent(values["parent_id"], store.id, db, category_id=category.id)
    if values.get("parent_id"):
        parent = db.get(Category, values["parent_id"])
        if parent is None or parent.store_id != store.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La categoría padre no pertenece a tu tienda")
    if "slug" in values and values["slug"]:
        values["slug"] = _slug(values["slug"])
        _ensure_unique_category_slug(store.id, values["slug"], db, exclude_id=category.id)
    for key, value in values.items():
        setattr(category, key, value)
    _commit_category(db)
    db.refresh(category)
    return _category_out(category)


@seller_router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar categoria de mi tienda",
    description=(
        "Rol permitido: seller. HU-CAT-01. Realiza baja logica de una categoria propia (`active=false`) "
        "para conservar historicos y ocultarla del catalogo publico."
    ),
    response_description="Categoria desactivada sin cuerpo de respuesta.",
    responses=CATEGORY_SELLER_RESPONSES,
)
def delete_category(category_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None or category.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    category.active = False
    db.commit()


@seller_router.get(
    "/products",
    response_model=ProductSellerListOut,
    status_code=status.HTTP_200_OK,
    summary="Listar mis productos",
    description=(
        "Rol permitido: seller. HU-PROD-01, HU-PROD-05, HU-PROD-06, HU-PROM-01 y HU-PROM-03. Lista productos de la tienda "
        "autenticada, incluidos borradores, agotados y descontinuados, con precio efectivo, costo interno y margen."
    ),
    response_description="Productos de la tienda autenticada con datos operativos seller.",
    responses=PRODUCT_SELLER_RESPONSES,
)
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
    return ProductSellerListOut(total=total, page=page, page_size=page_size, items=[ProductSellerOut.model_validate(_seller_product_out(row)) for row in rows])


def _seller_product(product_id: str, store: Store, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return product


@seller_router.post(
    "/products",
    response_model=ProductSellerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto de mi tienda",
    description=(
        "Rol permitido: seller. HU-PROD-01, HU-PROD-02, HU-PROD-04, HU-PROD-05, HU-PROM-01, HU-PROM-03 y HU-CAT-02. Crea un producto "
        "propio con variantes, precio regular/especial, costo interno, imagenes y estado inicial; puede asociarlo a "
        "categorias activas de la misma tienda."
    ),
    response_description="Producto creado con datos operativos seller.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def create_product(body: ProductIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    slug = _slug(body.slug or body.name)
    _ensure_unique_product_slug(store.id, slug, db)
    seen_skus: set[str] = set()
    for variant_data in body.variants:
        if variant_data.sku in seen_skus:
            raise HTTPException(status.HTTP_409_CONFLICT, "No repitas SKU dentro del producto")
        validate_special_price(
            regular_price=variant_data.price,
            special_price=variant_data.special_price,
            special_starts_at=variant_data.special_starts_at,
            special_ends_at=variant_data.special_ends_at,
        )
        seen_skus.add(variant_data.sku)
    product = Product(
        store_id=store.id,
        slug=slug,
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
    db.flush()
    for image_data in body.images:
        _validate_image_variant(product, image_data.variant_id, db)
        db.add(ProductImage(product_id=product.id, **image_data.model_dump()))
    _commit_product(db)
    db.refresh(product)
    return ProductSellerOut.model_validate(_seller_product_out(product))


def _replace_categories(product: Product, ids: list[str], store_id: str, db: Session) -> None:
    if len(ids) != len(set(ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No repitas categorias en category_ids")
    categories = db.scalars(select(Category).where(Category.id.in_(ids), Category.store_id == store_id, Category.active.is_(True))).all() if ids else []
    if len(categories) != len(set(ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Una categoría no pertenece a tu tienda")
    desired_ids = {category.id for category in categories}
    existing_ids = {link.category_id for link in product.category_links}
    for link in list(product.category_links):
        if link.category_id not in desired_ids:
            db.delete(link)
    for category in categories:
        if category.id not in existing_ids:
            product.category_links.append(ProductCategory(product_id=product.id, category_id=category.id))


@seller_router.patch(
    "/products/{product_id}",
    response_model=ProductSellerOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar producto de mi tienda",
    description=(
        "Rol permitido: seller. HU-PROD-01, HU-PROD-05, HU-PROD-06, HU-PROM-03 y HU-CAT-02. Actualiza datos del producto "
        "propio y, si `category_ids` viene en el payload, reemplaza sus categorias por categorias activas "
        "de la misma tienda."
    ),
    response_description="Producto actualizado con datos operativos seller.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def patch_product(product_id: str, body: ProductPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    values = body.model_dump(exclude_unset=True)
    category_ids = values.pop("category_ids", None)
    if "slug" in values and values["slug"]:
        values["slug"] = _slug(values["slug"])
        _ensure_unique_product_slug(store.id, values["slug"], db, exclude_id=product.id)
    if "status" in values:
        values["status"] = ProductStatus(values["status"])
    for key, value in values.items():
        setattr(product, key, value)
    if category_ids is not None:
        _replace_categories(product, category_ids, store.id, db)
    _commit_product(db)
    db.refresh(product)
    return ProductSellerOut.model_validate(_seller_product_out(product))


@seller_router.delete(
    "/products/{product_id}",
    response_model=ProductSellerOut,
    status_code=status.HTTP_200_OK,
    summary="Descontinuar producto",
    description="Rol permitido: seller. HU-PROD-01 y HU-PROD-06. Cambia el producto propio a `discontinued` como baja logica y lo oculta del catalogo publico.",
    response_description="Producto descontinuado conservado para panel seller e historicos.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def discontinue_product(product_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    product.status = ProductStatus.discontinued
    db.commit()
    db.refresh(product)
    return ProductSellerOut.model_validate(_seller_product_out(product))


@seller_router.post(
    "/products/{product_id}/variants",
    response_model=VariantSellerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear variante de producto",
    description="Rol permitido: seller. HU-PROD-02, HU-PROD-05, HU-PROM-01 y HU-PROM-03. Crea una variante propia con SKU unico, atributos, precio regular, precio especial temporal y costo interno.",
    response_description="Variante creada con stock, costo y margen seller.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def create_variant(product_id: str, body: VariantIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    _ensure_unique_variant_sku(product.id, body.sku, db)
    validate_special_price(
        regular_price=body.price,
        special_price=body.special_price,
        special_starts_at=body.special_starts_at,
        special_ends_at=body.special_ends_at,
    )
    variant = ProductVariant(product_id=product.id, **body.model_dump())
    db.add(variant)
    _commit_product(db)
    db.refresh(variant)
    return VariantSellerOut.model_validate(_variant_out(variant, include_internal=True, product_status=product.status))


@seller_router.patch(
    "/variants/{variant_id}",
    response_model=VariantSellerOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar variante de producto",
    description="Rol permitido: seller. HU-PROD-02, HU-PROD-05, HU-PROM-01 y HU-PROM-03. Actualiza una variante propia, incluido precio regular, precio especial temporal, costo interno y estado activo.",
    response_description="Variante actualizada con stock, costo y margen seller.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def patch_variant(variant_id: str, body: VariantPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    variant = _seller_variant(variant_id, store, db)
    values = body.model_dump(exclude_unset=True)
    if "sku" in values and values["sku"]:
        _ensure_unique_variant_sku(variant.product_id, values["sku"], db, exclude_id=variant.id)
    validate_special_price(
        regular_price=values.get("price", variant.price),
        special_price=values.get("special_price", variant.special_price),
        special_starts_at=values.get("special_starts_at", variant.special_starts_at),
        special_ends_at=values.get("special_ends_at", variant.special_ends_at),
    )
    for key, value in values.items():
        setattr(variant, key, value)
    _commit_product(db)
    db.refresh(variant)
    return VariantSellerOut.model_validate(_variant_out(variant, include_internal=True, product_status=variant.product.status))


@seller_router.delete(
    "/variants/{variant_id}",
    response_model=VariantSellerOut,
    status_code=status.HTTP_200_OK,
    summary="Desactivar variante de producto",
    description="Rol permitido: seller. HU-PROD-02. Realiza baja logica de una variante propia para que deje de estar disponible como opcion seleccionable.",
    response_description="Variante desactivada conservada para historial.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def delete_variant(variant_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    variant = _seller_variant(variant_id, store, db)
    variant.active = False
    db.commit()
    db.refresh(variant)
    return VariantSellerOut.model_validate(_variant_out(variant, include_internal=True, product_status=variant.product.status))


@seller_router.post(
    "/products/{product_id}/images",
    response_model=ProductImageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear imagen de producto",
    description="Rol permitido: seller. HU-PROD-04. Agrega una imagen general del producto o una imagen especifica de una variante del mismo producto.",
    response_description="Imagen creada y asociada al producto o variante.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def create_image(product_id: str, body: ImageIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    _validate_image_variant(product, body.variant_id, db)
    image = ProductImage(product_id=product.id, **body.model_dump())
    db.add(image)
    db.commit()
    db.refresh(image)
    return ProductImageOut.model_validate(_image_out(image))


@seller_router.patch(
    "/products/{product_id}/images/{image_id}",
    response_model=ProductImageOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar imagen de producto",
    description="Rol permitido: seller. HU-PROD-04. Actualiza URL, texto alternativo, orden o variante asociada de una imagen propia.",
    response_description="Imagen actualizada.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def patch_image(product_id: str, image_id: str, body: ImagePatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    product = _seller_product(product_id, store, db)
    image = _seller_image(product_id, image_id, store, db)
    values = body.model_dump(exclude_unset=True)
    if "variant_id" in values:
        _validate_image_variant(product, values["variant_id"], db)
    for key, value in values.items():
        setattr(image, key, value)
    db.commit()
    db.refresh(image)
    return ProductImageOut.model_validate(_image_out(image))


@seller_router.delete(
    "/products/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar imagen de producto",
    description="Rol permitido: seller. HU-PROD-04. Elimina una imagen propia para que deje de mostrarse en la ficha publica.",
    response_description="Imagen eliminada sin cuerpo de respuesta.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def delete_image(product_id: str, image_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    image = _seller_image(product_id, image_id, store, db)
    db.delete(image)
    db.commit()


IMPORT_COLUMNS = [
    "name",
    "slug",
    "description",
    "short_desc",
    "category_slug",
    "sku",
    "price",
    "cost",
    "stock",
    "status",
    "image_url",
]


def _cell_text(cell, shared_strings: list[str]) -> str:
    value = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        index = int(value.text)
        return shared_strings[index] if index < len(shared_strings) else ""
    return value.text


def _parse_xlsx_rows(content: bytes) -> list[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                texts = [node.text or "" for node in item.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]
                shared_strings.append("".join(texts))
        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in archive.namelist():
            raise ValueError("El archivo XLSX no contiene sheet1")
        root = ElementTree.fromstring(archive.read(sheet_name))
        rows = []
        for row in root.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            values = [_cell_text(cell, shared_strings).strip() for cell in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c")]
            rows.append(values)
    if not rows:
        return []
    headers = [header.strip() for header in rows[0]]
    return [dict(zip(headers, values, strict=False)) for values in rows[1:] if any(values)]


def _parse_import_rows(filename: str, content: bytes) -> list[dict[str, str]]:
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        return _parse_xlsx_rows(content)
    if lower.endswith(".csv") or lower.endswith(".txt"):
        text = content.decode("utf-8-sig")
        return [dict(row) for row in csv.DictReader(io.StringIO(text))]
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato no soportado. Usa CSV o XLSX")


def _int_field(value: str | None, field: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise ValueError(f"{field} debe ser un entero") from exc


@seller_router.get(
    "/products/import/template",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Descargar plantilla de productos",
    description="Rol permitido: seller. HU-PROD-03. Devuelve una plantilla CSV con columnas esperadas para carga masiva de productos.",
    response_description="Archivo CSV de ejemplo para importacion.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def product_import_template(_store: Store = Depends(get_seller_store)):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=IMPORT_COLUMNS)
    writer.writeheader()
    writer.writerow(
        {
            "name": "Camisa negra",
            "slug": "camisa-negra",
            "description": "Camisa de algodon.",
            "short_desc": "Camisa basica de algodon.",
            "category_slug": "camisas",
            "sku": "CAM-NEG-S",
            "price": "70000",
            "cost": "30000",
            "stock": "12",
            "status": "active",
            "image_url": "https://cdn.example.com/products/camisa.jpg",
        }
    )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="productos_template.csv"'},
    )


@seller_router.post(
    "/products/import",
    response_model=ProductImportResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importar productos",
    description="Rol permitido: seller. HU-PROD-03. Procesa un archivo CSV/XLSX, crea filas validas y reporta errores por fila sin abortar todo el lote.",
    response_description="Resumen de productos creados y errores por fila.",
    responses=PRODUCT_SELLER_RESPONSES,
)
def import_products(file: UploadFile = File(...), store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    """Importa productos desde CSV/XLSX con errores por fila."""
    warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True), Warehouse.is_default.is_(True)))
    if warehouse is None:
        warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True)).order_by(Warehouse.name))
    if warehouse is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes registrar un almacén antes de importar inventario")

    try:
        raw_rows = _parse_import_rows(file.filename or "", file.file.read())
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if not raw_rows:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo no contiene filas para importar")
    missing = {"name", "sku", "price"} - set(raw_rows[0].keys())
    if missing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Faltan columnas obligatorias: {', '.join(sorted(missing))}")

    created: list[Product] = []
    errors: list[dict] = []
    seen_slugs: set[str] = set()
    for index, raw in enumerate(raw_rows, start=2):
        try:
            normalized = {key: (value.strip() if isinstance(value, str) else value) for key, value in raw.items()}
            price = _int_field(normalized.get("price"), "price")
            cost = _int_field(normalized.get("cost"), "cost")
            stock = _int_field(normalized.get("stock"), "stock") or 0
            data = ProductImportRow(
                name=normalized.get("name") or "",
                slug=normalized.get("slug") or None,
                description=normalized.get("description") or None,
                short_desc=normalized.get("short_desc") or None,
                category_slug=normalized.get("category_slug") or None,
                sku=normalized.get("sku") or "",
                price=price,
                cost=cost,
                stock=stock,
                status=normalized.get("status") or "draft",
                image_url=normalized.get("image_url") or None,
            )
            slug = _slug(data.slug or data.name)
            if slug in seen_slugs or db.scalar(select(Product).where(Product.store_id == store.id, Product.slug == slug)) is not None:
                raise ValueError("slug duplicado en la tienda o en el archivo")
            seen_slugs.add(slug)
            category = None
            if data.category_slug:
                category = db.scalar(
                    select(Category).where(
                        Category.store_id == store.id,
                        Category.slug == data.category_slug,
                        Category.active.is_(True),
                    )
                )
                if category is None:
                    raise ValueError("category_slug no pertenece a tu tienda o esta inactiva")
        except ValidationError as exc:
            errors.append({"row": index, "field": ".".join(str(part) for part in exc.errors()[0]["loc"]), "message": exc.errors()[0]["msg"]})
            continue
        except ValueError as exc:
            errors.append({"row": index, "field": None, "message": str(exc)})
            continue

        product = Product(
            store_id=store.id,
            slug=slug,
            name=data.name,
            short_desc=data.short_desc,
            description=data.description,
            status=ProductStatus(data.status),
        )
        db.add(product)
        db.flush()
        variant = ProductVariant(product_id=product.id, sku=data.sku, price=data.price, cost=data.cost)
        db.add(variant)
        db.flush()
        if category is not None:
            product.category_links.append(ProductCategory(product_id=product.id, category_id=category.id))
        if data.image_url:
            db.add(ProductImage(product_id=product.id, url=data.image_url, alt=data.name, sort_order=0))
        db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=data.stock))
        db.add(InventoryMovement(variant_id=variant.id, warehouse_id=warehouse.id, delta=data.stock, reason=InventoryReason.restock, note="Importacion masiva"))
        created.append(product)
    _commit_product(db)
    for product in created:
        db.refresh(product)
    return ProductImportResultOut(
        created_count=len(created),
        error_count=len(errors),
        items=[ProductSellerOut.model_validate(_seller_product_out(product)) for product in created],
        errors=[ProductImportErrorOut.model_validate(error) for error in errors],
    )
