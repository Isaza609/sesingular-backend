from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SOCIAL_LINK_PREFIXES = ("http://", "https://")


def _validate_social_links(value: dict[str, Any] | None) -> dict[str, str]:
    if not value:
        return {}
    cleaned: dict[str, str] = {}
    for network, url in value.items():
        if not isinstance(network, str) or not network.strip():
            raise ValueError("El nombre de la red social es obligatorio")
        if not isinstance(url, str) or not url.strip().startswith(SOCIAL_LINK_PREFIXES):
            raise ValueError(f"El enlace de {network} debe iniciar con http:// o https://")
        cleaned[network.strip().lower()] = url.strip()
    return cleaned


class CategoryIn(BaseModel):
    name: str = Field(description="Nombre visible de la categoria propia de la tienda.", min_length=1, max_length=200, example="Aretes")
    slug: str | None = Field(default=None, description="Slug opcional; si no se envia se genera desde el nombre.", max_length=120, example="aretes")
    parent_id: str | None = Field(default=None, description="Categoria padre de la misma tienda; null crea categoria raiz.", example=None)
    sort_order: int = Field(default=0, description="Orden relativo dentro del catalogo de la tienda.", ge=0, example=10)
    active: bool = Field(default=True, description="Indica si aparece en el catalogo publico.", example=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Aretes",
                "slug": "aretes",
                "parent_id": None,
                "sort_order": 10,
                "active": True,
            }
        }
    )


class CategoryPatch(CategoryIn):
    name: str | None = Field(default=None, description="Nuevo nombre visible de la categoria.", min_length=1, max_length=200, example="Aretes dorados")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Aretes dorados",
                "parent_id": None,
                "sort_order": 20,
                "active": True,
            }
        }
    )


class VariantIn(BaseModel):
    sku: str = Field(description="SKU unico dentro del producto.", min_length=1, max_length=80, example="CAM-S-NEG")
    name: str | None = Field(default=None, description="Nombre opcional de la variante o presentacion.", max_length=200, example="Camisa negra talla S")
    color: str | None = Field(default=None, description="Color de la variante.", max_length=80, example="Negro")
    size: str | None = Field(default=None, description="Talla o medida de la variante.", max_length=80, example="S")
    price: int = Field(description="Precio de venta de esta variante en COP.", ge=0, example=70000)
    compare_at: int | None = Field(default=None, description="Precio de referencia o antes.", ge=0, example=85000)
    cost: int | None = Field(default=None, description="Costo interno de materiales o produccion; solo visible para seller.", ge=0, example=30000)
    special_price: int | None = Field(default=None, description="Precio especial temporal en COP.", ge=0, example=60000)
    special_starts_at: datetime | None = Field(default=None, description="Inicio de vigencia del precio especial.", example="2026-08-01T00:00:00Z")
    special_ends_at: datetime | None = Field(default=None, description="Fin de vigencia del precio especial.", example="2026-08-15T23:59:59Z")
    active: bool = Field(default=True, description="Indica si la variante puede mostrarse como opcion.", example=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku": "CAM-S-NEG",
                "name": "Camisa negra talla S",
                "color": "Negro",
                "size": "S",
                "price": 70000,
                "compare_at": 85000,
                "cost": 30000,
                "special_price": 60000,
                "special_starts_at": "2026-08-01T00:00:00Z",
                "special_ends_at": "2026-08-15T23:59:59Z",
                "active": True,
            }
        }
    )


class VariantPatch(VariantIn):
    sku: str | None = Field(default=None, description="Nuevo SKU unico dentro del producto.", min_length=1, max_length=80, example="CAM-S-BLA")
    price: int | None = Field(default=None, description="Nuevo precio de venta en COP.", ge=0, example=72000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku": "CAM-S-BLA",
                "color": "Blanco",
                "size": "S",
                "price": 72000,
                "special_price": 65000,
                "special_starts_at": "2026-08-01T00:00:00Z",
                "special_ends_at": "2026-08-15T23:59:59Z",
                "cost": 31000,
                "active": True,
            }
        }
    )


class ImageIn(BaseModel):
    url: str = Field(description="URL publica de la imagen del producto.", min_length=1, max_length=500, example="https://cdn.example.com/products/camisa-frente.jpg")
    alt: str | None = Field(default=None, description="Texto alternativo de la imagen.", max_length=200, example="Camisa negra vista frontal")
    sort_order: int = Field(default=0, description="Orden de la imagen en la galeria.", ge=0, example=10)
    variant_id: str | None = Field(default=None, description="Variante especifica asociada a la imagen; null indica imagen general del producto.", example=None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://cdn.example.com/products/camisa-frente.jpg",
                "alt": "Camisa negra vista frontal",
                "sort_order": 10,
                "variant_id": None,
            }
        }
    )


class ImagePatch(BaseModel):
    url: str | None = Field(default=None, description="Nueva URL publica de la imagen.", min_length=1, max_length=500, example="https://cdn.example.com/products/camisa-lateral.jpg")
    alt: str | None = Field(default=None, description="Nuevo texto alternativo.", max_length=200, example="Camisa negra vista lateral")
    sort_order: int | None = Field(default=None, description="Nuevo orden en la galeria.", ge=0, example=20)
    variant_id: str | None = Field(default=None, description="Nueva variante asociada; null mueve la imagen a galeria general.", example=None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alt": "Camisa negra vista lateral",
                "sort_order": 20,
                "variant_id": "variant-camisa-s",
            }
        }
    )


class ProductImageOut(BaseModel):
    id: str = Field(description="Identificador de la imagen.", example="img-123")
    url: str = Field(description="URL publica de la imagen.", example="https://cdn.example.com/products/camisa-frente.jpg")
    alt: str | None = Field(default=None, description="Texto alternativo.", example="Camisa negra vista frontal")
    sort_order: int = Field(description="Orden en la galeria.", example=10)
    variant_id: str | None = Field(default=None, description="Variante asociada o null para imagen general.", example=None)


class VariantPublicOut(BaseModel):
    id: str = Field(description="Identificador de la variante.", example="variant-camisa-s")
    sku: str = Field(description="SKU de la variante.", example="CAM-S-NEG")
    name: str | None = Field(default=None, description="Nombre o presentacion de la variante.", example="Camisa negra talla S")
    color: str | None = Field(default=None, description="Color.", example="Negro")
    size: str | None = Field(default=None, description="Talla o medida.", example="S")
    price: int = Field(description="Precio efectivo de venta de la variante.", example=60000)
    regular_price: int = Field(description="Precio regular de la variante antes de ofertas temporales.", example=70000)
    compare_at: int | None = Field(default=None, description="Precio de referencia.", example=85000)
    special_price: int | None = Field(default=None, description="Precio especial configurado cuando existe.", example=60000)
    special_starts_at: datetime | None = Field(default=None, description="Inicio de vigencia del precio especial.", example="2026-08-01T00:00:00Z")
    special_ends_at: datetime | None = Field(default=None, description="Fin de vigencia del precio especial.", example="2026-08-15T23:59:59Z")
    special_price_active: bool = Field(description="Indica si el precio efectivo corresponde al precio especial vigente.", example=True)
    active: bool = Field(description="Indica si la variante esta activa.", example=True)
    stock: int = Field(description="Stock disponible agregado.", example=5)
    available: bool = Field(description="Indica si se puede seleccionar/comprar.", example=True)
    images: list[ProductImageOut] = Field(default_factory=list, description="Imagenes especificas de esta variante.")


class VariantSellerOut(VariantPublicOut):
    cost: int | None = Field(default=None, description="Costo interno de materiales o produccion.", example=30000)
    margin: int | None = Field(default=None, description="Margen bruto calculado como precio menos costo.", example=40000)
    margin_pct: float | None = Field(default=None, description="Porcentaje de margen sobre precio.", example=57.14)
    margin_missing_cost: bool = Field(description="Indica si falta costo interno para calcular margen.", example=False)


class ProductIn(BaseModel):
    name: str = Field(description="Nombre del producto publicado por la tienda.", min_length=1, max_length=300, example="Aretes Luna")
    slug: str | None = Field(default=None, description="Slug opcional; si no se envia se genera desde el nombre.", max_length=160, example="aretes-luna")
    short_desc: str | None = Field(default=None, description="Resumen corto para tarjetas de catalogo.", max_length=500, example="Aretes livianos con acabado dorado.")
    description: str | None = Field(default=None, description="Descripcion completa del producto.", example="Pieza hecha a mano para uso diario.")
    material: str | None = Field(default=None, description="Material principal visible en catalogo.", max_length=120, example="Acero inoxidable")
    badge: str | None = Field(default=None, description="Etiqueta comercial visible en catalogo.", pattern="^(nuevo|destacado|oferta)$", example="nuevo")
    bestseller: bool = Field(default=False, description="Marca el producto como destacado por ventas.", example=False)
    status: str = Field(default="draft", description="Estado operativo del producto.", pattern="^(draft|active|out_of_stock|discontinued)$", example="active")
    category_ids: list[str] = Field(
        default_factory=list,
        description="Categorias o subcategorias activas de la misma tienda donde aparece el producto. No permite ids duplicados.",
        example=["cat-aretes", "cat-regalos"],
    )
    variants: list[VariantIn] = Field(min_length=1)
    images: list[ImageIn] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Aretes Luna",
                "slug": "aretes-luna",
                "short_desc": "Aretes livianos con acabado dorado.",
                "description": "Pieza hecha a mano para uso diario.",
                "material": "Acero inoxidable",
                "badge": "nuevo",
                "bestseller": False,
                "status": "active",
                "category_ids": ["cat-aretes", "cat-regalos"],
                "variants": [{"sku": "AR-LUNA", "price": 45000, "active": True}],
                "images": [{"url": "https://cdn.example.com/products/aretes-luna.jpg", "alt": "Aretes Luna"}],
            }
        }
    )


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, description="Nuevo nombre del producto.", min_length=1, max_length=300, example="Aretes Luna dorados")
    slug: str | None = Field(default=None, description="Nuevo slug del producto.", max_length=160, example="aretes-luna-dorados")
    short_desc: str | None = Field(default=None, description="Nuevo resumen corto.", max_length=500, example="Aretes dorados para regalo.")
    description: str | None = Field(default=None, description="Nueva descripcion completa.", example="Pieza hecha a mano para uso diario.")
    material: str | None = Field(default=None, description="Material principal visible en catalogo.", max_length=120, example="Acero inoxidable")
    badge: str | None = Field(default=None, description="Etiqueta comercial visible en catalogo.", pattern="^(nuevo|destacado|oferta)$", example="destacado")
    bestseller: bool | None = Field(default=None, description="Marca o desmarca el producto como destacado.", example=True)
    status: str | None = Field(default=None, description="Nuevo estado operativo del producto.", pattern="^(draft|active|out_of_stock|discontinued)$", example="active")
    category_ids: list[str] | None = Field(
        default=None,
        description="Si se envia, reemplaza todas las categorias del producto por categorias activas de la misma tienda.",
        example=["cat-aretes"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_ids": ["cat-aretes"],
                "status": "active",
            }
        }
    )


class ProductOut(BaseModel):
    id: str = Field(description="Identificador del producto.", example="prod-camisa")
    store_id: str = Field(description="Tienda propietaria.", example="store-nova")
    store_name: str = Field(description="Nombre publico de la tienda.", example="Nova Ropa")
    slug: str = Field(description="Slug unico dentro de la tienda.", example="camisa-negra")
    name: str = Field(description="Nombre publico del producto.", example="Camisa negra")
    short_desc: str | None = Field(default=None, description="Resumen corto para catalogo.", example="Camisa basica de algodon.")
    description: str | None = Field(default=None, description="Descripcion completa.", example="Camisa comoda para uso diario.")
    material: str | None = Field(default=None, description="Material visible al comprador.", example="Algodon")
    badge: str | None = Field(default=None, description="Etiqueta comercial.", example="nuevo")
    bestseller: bool = Field(default=False, description="Marca de destacado por ventas.", example=False)
    status: str = Field(description="Estado visible del producto.", example="active")
    categories: list[dict] = Field(description="Categorias activas asignadas.", example=[{"id": "cat-camisas", "slug": "camisas", "name": "Camisas"}])
    variants: list[VariantPublicOut] = Field(description="Variantes publicas sin costo interno.")
    images: list[ProductImageOut] = Field(description="Galeria general del producto.")
    stock: int = Field(description="Stock disponible agregado.", example=5)
    price: int = Field(description="Precio inicial o minimo mostrado.", example=70000)
    compare_at: int | None = Field(default=None, description="Precio de referencia inicial.", example=85000)
    created_at: datetime = Field(description="Fecha de creacion.")
    updated_at: datetime = Field(description="Fecha de actualizacion.")


class ProductSellerOut(ProductOut):
    variants: list[VariantSellerOut] = Field(description="Variantes con costo interno y margen para seller.")


class ProductListOut(BaseModel):
    total: int = Field(description="Total de productos encontrados.", example=1)
    page: int = Field(description="Pagina actual.", example=1)
    page_size: int = Field(description="Cantidad de resultados por pagina.", example=24)
    items: list[ProductOut] = Field(description="Productos de la pagina.")


class ProductSellerListOut(BaseModel):
    total: int = Field(description="Total de productos encontrados.", example=1)
    page: int = Field(description="Pagina actual.", example=1)
    page_size: int = Field(description="Cantidad de resultados por pagina.", example=24)
    items: list[ProductSellerOut] = Field(description="Productos seller de la pagina.")


class StorePublicOut(BaseModel):
    id: str = Field(description="Identificador de la tienda.", example="store-123")
    slug: str = Field(description="Slug publico de la tienda.", example="nova-ropa")
    name: str = Field(description="Nombre publico administrado de la tienda.", example="Nova Ropa")
    description: str | None = Field(default=None, description="Descripcion publica de la tienda.", example="Moda local para todos los dias.")
    logo_url: str | None = Field(default=None, description="URL del logo publico.", example="https://cdn.example.com/nova/logo.png")
    contact_email: str | None = Field(default=None, description="Correo publico de contacto.", example="hola@nova.example")
    contact_phone: str | None = Field(default=None, description="Telefono publico de contacto.", example="+573001112233")
    whatsapp_phone: str | None = Field(default=None, description="Telefono publico de WhatsApp.", example="+573001112233")
    social_links: dict[str, str] = Field(default_factory=dict, description="Enlaces publicos a redes sociales.", example={"instagram": "https://instagram.com/nova"})


class SellerStoreOut(StorePublicOut):
    active: bool = Field(description="Indica si la tienda esta activa; campo administrado.", example=True)


class SellerStorePatch(BaseModel):
    description: str | None = Field(default=None, description="Descripcion publica actualizada.", example="Ropa comoda producida localmente.")
    logo_url: str | None = Field(default=None, description="URL actualizada del logo publico.", max_length=500, example="https://cdn.example.com/nova/logo-v2.png")
    contact_email: str | None = Field(default=None, description="Correo publico de contacto.", pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", example="contacto@nova.example")
    contact_phone: str | None = Field(default=None, description="Telefono publico de contacto.", max_length=40, example="+573001112233")
    whatsapp_phone: str | None = Field(default=None, description="Telefono publico de WhatsApp.", max_length=40, example="+573001112233")
    social_links: dict[str, str] = Field(default_factory=dict, description="Enlaces publicos a redes sociales.", example={"instagram": "https://instagram.com/nova"})

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "description": "Ropa comoda producida localmente.",
                "logo_url": "https://cdn.example.com/nova/logo-v2.png",
                "contact_email": "contacto@nova.example",
                "contact_phone": "+573001112233",
                "whatsapp_phone": "+573001112233",
                "social_links": {"instagram": "https://instagram.com/nova"},
            }
        },
    )

    @field_validator("social_links")
    @classmethod
    def social_links_must_be_urls(cls, value: dict[str, Any] | None) -> dict[str, str]:
        return _validate_social_links(value)


class PaymentMethodsConfig(BaseModel):
    gateway_enabled: bool = Field(default=True, description="Indica si la tienda acepta pasarela automatizada.", example=True)
    manual_transfer_enabled: bool = Field(default=True, description="Indica si la tienda acepta transferencia bancaria.", example=True)
    manual_breb_enabled: bool = Field(default=True, description="Indica si la tienda acepta Bre-B.", example=False)

    model_config = {
        "json_schema_extra": {
            "example": {
                "gateway_enabled": True,
                "manual_transfer_enabled": True,
                "manual_breb_enabled": False,
            }
        }
    }


class StoreSettingsIn(BaseModel):
    payment_methods: PaymentMethodsConfig = Field(default_factory=PaymentMethodsConfig, description="Metodos de pago aceptados por la tienda.")
    shipping_flat_cost: int = Field(default=12900, description="Costo plano de envio de la tienda.", ge=0, example=12900)
    shipping_free_threshold: int = Field(default=120000, description="Subtotal desde el cual el envio es gratis.", ge=0, example=120000)
    shipping_zones: list[dict] = Field(default_factory=list, description="Zonas de envio configuradas por la tienda.", example=[])

    model_config = {
        "json_schema_extra": {
            "example": {
                "payment_methods": {
                    "gateway_enabled": True,
                    "manual_transfer_enabled": True,
                    "manual_breb_enabled": False,
                },
                "shipping_flat_cost": 12900,
                "shipping_free_threshold": 120000,
                "shipping_zones": [],
            }
        }
    }

    @field_validator("payment_methods", mode="before")
    @classmethod
    def normalize_legacy_payment_methods(cls, value):
        if isinstance(value, list):
            legacy = set(value)
            return {
                "gateway_enabled": bool({"card", "pse", "nequi", "gateway"} & legacy),
                "manual_transfer_enabled": "transfer" in legacy,
                "manual_breb_enabled": "breb" in legacy,
            }
        return value or {}


class StoreSettingsOut(StoreSettingsIn):
    pass


class PayoutAccountPublicOut(BaseModel):
    id: str = Field(description="Identificador de la cuenta de cobro.", example="acct-123")
    type: str = Field(description="Tipo de cuenta manual: bank o bre_b.", example="bank")
    label: str | None = Field(default=None, description="Etiqueta visible para comprador.", example="Bancolombia principal")
    bank_name: str | None = Field(default=None, description="Nombre del banco para transferencia.", example="Bancolombia")
    account_type: str | None = Field(default=None, description="Tipo de cuenta bancaria.", example="ahorros")
    account_number: str | None = Field(default=None, description="Numero de cuenta bancaria.", example="123456789")
    breb_key: str | None = Field(default=None, description="Llave Bre-B.", example="nova@breb")
    holder_name: str = Field(description="Nombre del titular.", example="Nova Ropa SAS")
    holder_document: str | None = Field(default=None, description="Documento del titular.", example="900123456")


class StorePaymentOptionsOut(BaseModel):
    store_id: str = Field(description="Identificador de la tienda.", example="store-123")
    store_name: str = Field(description="Nombre publico de la tienda.", example="Nova Ropa")
    payment_methods: list[str] = Field(description="Metodos disponibles para comprador en checkout.", example=["transfer", "breb"])
    payout_accounts: list[PayoutAccountPublicOut] = Field(description="Cuentas manuales activas disponibles para los metodos listados.")


class StoreListPublicOut(BaseModel):
    items: list[StorePublicOut]


class CategoryOut(BaseModel):
    id: str = Field(description="Identificador de la categoria.", example="cat-aretes")
    store_id: str = Field(description="Tienda propietaria de la categoria.", example="store-nova")
    parent_id: str | None = Field(default=None, description="Categoria padre de la misma tienda; null indica raiz.", example=None)
    slug: str = Field(description="Slug unico dentro de la tienda.", example="aretes")
    name: str = Field(description="Nombre visible de la categoria.", example="Aretes")
    sort_order: int = Field(description="Orden relativo dentro del catalogo.", example=10)
    active: bool = Field(description="Indica si aparece en catalogo publico.", example=True)


class ProductImportRow(BaseModel):
    """Contrato comun para carga CSV/XLSX desde el panel vendedor."""

    name: str = Field(description="Nombre del producto.", min_length=1, example="Camisa negra")
    sku: str = Field(description="SKU de la variante principal.", min_length=1, example="CAM-NEG-S")
    price: int = Field(description="Precio de venta de la variante.", ge=0, example=70000)
    cost: int | None = Field(default=None, description="Costo interno de produccion.", ge=0, example=30000)
    stock: int = Field(default=0, description="Stock inicial para el almacen activo.", ge=0, example=12)
    category_slug: str | None = Field(default=None, description="Slug de categoria activa de la misma tienda.", example="camisas")
    slug: str | None = Field(default=None, description="Slug opcional del producto.", max_length=160, example="camisa-negra")
    description: str | None = Field(default=None, description="Descripcion completa.", example="Camisa de algodon.")
    short_desc: str | None = Field(default=None, description="Resumen corto.", max_length=500, example="Camisa basica de algodon.")
    status: str = Field(default="draft", description="Estado inicial del producto.", pattern="^(draft|active|out_of_stock|discontinued)$", example="active")
    image_url: str | None = Field(default=None, description="URL opcional de imagen principal.", max_length=500, example="https://cdn.example.com/products/camisa.jpg")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Camisa negra",
                "slug": "camisa-negra",
                "description": "Camisa de algodon.",
                "category_slug": "camisas",
                "sku": "CAM-NEG-S",
                "price": 70000,
                "cost": 30000,
                "stock": 12,
                "status": "active",
                "image_url": "https://cdn.example.com/products/camisa.jpg",
            }
        }
    )


class ProductImportErrorOut(BaseModel):
    row: int = Field(description="Numero de fila del archivo, incluyendo encabezado en fila 1.", example=3)
    field: str | None = Field(default=None, description="Campo asociado al error cuando aplica.", example="price")
    message: str = Field(description="Motivo funcional del rechazo de la fila.", example="price debe ser un entero mayor o igual a cero")


class ProductImportResultOut(BaseModel):
    created_count: int = Field(description="Cantidad de productos creados.", example=2)
    error_count: int = Field(description="Cantidad de filas rechazadas.", example=1)
    row_contract: ProductImportRow | None = Field(
        default=None,
        description="Referencia del contrato de columnas aceptado por la carga CSV/XLSX.",
    )
    items: list[ProductSellerOut] = Field(description="Productos creados correctamente.")
    errors: list[ProductImportErrorOut] = Field(description="Errores por fila.")
