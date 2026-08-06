from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AddressIn(BaseModel):
    label: str | None = Field(default=None, description="Etiqueta visible para el comprador.", max_length=80, example="Casa")
    recipient_name: str = Field(description="Nombre de quien recibe el envio.", min_length=1, max_length=200, example="Ana Perez")
    phone: str | None = Field(default=None, description="Telefono de contacto para la entrega.", max_length=40, example="+573001112233")
    address_line: str = Field(description="Direccion completa de entrega.", min_length=1, max_length=300, example="Calle 10 # 20-30")
    city: str = Field(description="Ciudad o municipio de entrega.", min_length=1, max_length=120, example="Bogota")
    region: str | None = Field(default=None, description="Departamento, provincia o region.", max_length=120, example="Cundinamarca")
    postal_code: str | None = Field(default=None, description="Codigo postal opcional.", max_length=20, example="110111")
    is_default: bool = Field(default=False, description="Indica si sera la direccion por defecto.", example=True)

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "Casa",
                "recipient_name": "Ana Perez",
                "phone": "+573001112233",
                "address_line": "Calle 10 # 20-30",
                "city": "Bogota",
                "region": "Cundinamarca",
                "postal_code": "110111",
                "is_default": True,
            }
        }
    }


class AddressPatch(AddressIn):
    recipient_name: str | None = Field(default=None, description="Nombre actualizado de quien recibe.", min_length=1, max_length=200, example="Ana Maria Perez")
    address_line: str | None = Field(default=None, description="Direccion completa actualizada.", min_length=1, max_length=300, example="Carrera 15 # 80-20")
    city: str | None = Field(default=None, description="Ciudad o municipio actualizado.", min_length=1, max_length=120, example="Medellin")

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "Apartamento",
                "recipient_name": "Ana Maria Perez",
                "phone": "+573004445566",
                "address_line": "Carrera 15 # 80-20",
                "city": "Medellin",
                "region": "Antioquia",
                "postal_code": "050021",
                "is_default": True,
            }
        }
    }


class AddressOut(BaseModel):
    id: str = Field(description="Identificador de la direccion.", example="addr-123")
    label: str | None = Field(default=None, description="Etiqueta visible para el comprador.", example="Casa")
    recipient_name: str = Field(description="Nombre de quien recibe el envio.", example="Ana Perez")
    phone: str | None = Field(default=None, description="Telefono de contacto para la entrega.", example="+573001112233")
    address_line: str = Field(description="Direccion completa de entrega.", example="Calle 10 # 20-30")
    city: str = Field(description="Ciudad o municipio de entrega.", example="Bogota")
    region: str | None = Field(default=None, description="Departamento, provincia o region.", example="Cundinamarca")
    postal_code: str | None = Field(default=None, description="Codigo postal opcional.", example="110111")
    is_default: bool = Field(description="Indica si es la direccion por defecto.", example=True)


class CartItemIn(BaseModel):
    variant_id: str | None = Field(default=None, description="Variante especifica a agregar al carrito.", example="variant-123")
    product_id: str | None = Field(default=None, description="Producto a resolver automaticamente cuando no se envia variant_id.", example="product-123")
    color: str | None = Field(default=None, description="Color preferido para resolver la variante.", example="rojo")
    quantity: int = Field(description="Cantidad solicitada.", ge=1, le=100, example=2)

    @model_validator(mode="after")
    def variant_or_product(self):
        if not self.variant_id and not self.product_id:
            raise ValueError("Debes indicar variant_id o product_id")
        return self


class CartItemPatch(BaseModel):
    quantity: int = Field(description="Nueva cantidad del item en carrito.", ge=1, le=100, example=3)


class ShippingLocationIn(BaseModel):
    city: str | None = Field(default=None, description="Ciudad o municipio usado para cotizar envio.", max_length=120, example="Bogota")
    region: str | None = Field(default=None, description="Departamento o region usado para cotizar envio.", max_length=120, example="Cundinamarca")
    country: str | None = Field(default=None, description="Pais usado para cotizar envio.", max_length=80, example="Colombia")

    model_config = {
        "json_schema_extra": {
            "example": {"city": "Bogota", "region": "Cundinamarca", "country": "Colombia"}
        }
    }


class CartItemOut(BaseModel):
    id: str = Field(description="Identificador del item en carrito.", example="cart-item-123")
    variant_id: str = Field(description="Variante agregada al carrito.", example="variant-123")
    product_id: str = Field(description="Producto asociado a la variante.", example="product-123")
    slug: str = Field(description="Slug publico del producto.", example="camisa-negra")
    name: str = Field(description="Nombre publico del producto.", example="Camisa negra")
    sku: str | None = Field(default=None, description="SKU de la variante.", example="CAM-S-NEG")
    color: str | None = Field(default=None, description="Color de la variante.", example="Negro")
    image: str | None = Field(default=None, description="Imagen principal del producto.", example="https://cdn.example.com/camisa.jpg")
    quantity: int = Field(description="Cantidad solicitada por el comprador.", example=2)
    unit_price: int = Field(description="Precio unitario efectivo en COP.", example=60000)
    regular_unit_price: int = Field(description="Precio regular unitario en COP.", example=70000)
    special_price_applied: bool = Field(description="Indica si aplica precio especial.", example=True)
    stock: int = Field(description="Stock disponible actual agregado.", example=5)
    available: bool = Field(description="Indica si el item puede pasar a checkout.", example=True)
    availability_status: str = Field(description="Estado de disponibilidad del item.", example="available")
    availability_message: str | None = Field(default=None, description="Mensaje visible cuando el item bloquea checkout.", example=None)
    store_id: str = Field(description="Tienda vendedora del item.", example="store-123")
    store_name: str = Field(description="Nombre publico de la tienda.", example="Nova Ropa")


class CartStoreGroupOut(BaseModel):
    store_id: str = Field(description="Tienda del grupo.", example="store-123")
    store_name: str = Field(description="Nombre publico de la tienda.", example="Nova Ropa")
    items: list[CartItemOut] = Field(description="Items del carrito vendidos por esta tienda.")
    regular_subtotal: int = Field(description="Subtotal regular del grupo.", example=140000)
    subtotal: int = Field(description="Subtotal efectivo del grupo.", example=120000)


class CheckoutContactOut(BaseModel):
    email: str | None = Field(default=None, description="Correo publico de contacto de la tienda.", example="hola@nova.example")
    phone: str | None = Field(default=None, description="Telefono publico de la tienda.", example="+573001112233")
    whatsapp_phone: str | None = Field(default=None, description="WhatsApp publico de la tienda.", example="+573001112233")


class CheckoutShippingOut(BaseModel):
    mode: str = Field(description="Modalidad de envio aplicada: flat, zones o to_agree.", example="zones")
    cost: int = Field(description="Costo de envio incluido en el total en COP.", example=12000)
    original_cost: int = Field(description="Costo antes de envio gratis o promocion.", example=12000)
    to_agree: bool = Field(description="Indica si el costo debe acordarse con el vendedor.", example=False)
    requires_contact: bool = Field(description="Indica si el comprador debe contactar al vendedor.", example=False)
    promotion_applied: bool = Field(description="Indica si el envio quedo gratis por promocion/umbral.", example=False)
    label: str | None = Field(default=None, description="Etiqueta de zona o modalidad aplicada.", example="Bogota")
    message: str | None = Field(default=None, description="Mensaje visible para el comprador.", example=None)


class CheckoutQuoteIn(BaseModel):
    address_id: str | None = Field(default=None, description="Direccion guardada del comprador para cotizar envio.", example="addr-123")
    address: AddressIn | None = Field(default=None, description="Direccion nueva usada para cotizar sin confirmar.")
    shipping_location: ShippingLocationIn | None = Field(default=None, description="Lugar usado para cotizar envio cuando aun no hay direccion.")
    coupon_code: str | None = Field(default=None, description="Codigo de cupon opcional.", example="VERANO10")
    payment_method: str | None = Field(default=None, description="Metodo de pago seleccionado para validar disponibilidad.", example="card")

    model_config = {
        "json_schema_extra": {
            "example": {
                "address_id": "addr-123",
                "shipping_location": {"city": "Bogota", "region": "Cundinamarca", "country": "Colombia"},
                "coupon_code": "VERANO10",
                "payment_method": "card",
            }
        }
    }


class CheckoutIn(BaseModel):
    address_id: str | None = Field(default=None, description="Direccion guardada del comprador.", example="addr-123")
    address: AddressIn | None = Field(default=None, description="Direccion nueva a crear y usar en el checkout.")
    coupon_code: str | None = Field(default=None, description="Codigo de cupon opcional.", example="VERANO10")
    payment_method: str = Field(default="card", description="Metodo de pago seleccionado.", min_length=1, max_length=60, example="card")
    # Cuenta de cobro elegida cuando el método es manual (transfer | breb)
    payout_account_id: str | None = Field(default=None, description="Cuenta de cobro manual elegida cuando el metodo lo requiere.", example="payout-123")
    notes: str | None = Field(default=None, description="Notas opcionales del comprador.", example="Entregar en porteria")

    @model_validator(mode="after")
    def address_required(self):
        if not self.address_id and not self.address:
            raise ValueError("Debes seleccionar o registrar una dirección")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "address_id": "addr-123",
                "coupon_code": "VERANO10",
                "payment_method": "card",
                "payout_account_id": None,
                "notes": "Entregar en porteria",
            }
        }
    }


class OrderStatusPatch(BaseModel):
    status: str = Field(description="Nuevo estado del pedido.", pattern="^(pending|confirmed|preparing|shipped|delivered|cancelled|returned)$", example="cancelled")

    model_config = {
        "json_schema_extra": {
            "example": {"status": "cancelled"}
        }
    }


class WarehouseAssign(BaseModel):
    warehouse_id: str = Field(description="Almacen activo de la tienda desde el cual se despachara el pedido.", example="wh-123")

    model_config = {
        "json_schema_extra": {
            "example": {"warehouse_id": "wh-123"}
        }
    }


class OrderItemOut(BaseModel):
    id: str = Field(description="Identificador historico del item de pedido.", example="item-123")
    variant_id: str | None = Field(default=None, description="Variante vendida.", example="variant-123")
    product_name: str = Field(description="Nombre historico del producto vendido.", example="Collar tejido")
    sku: str | None = Field(default=None, description="SKU historico de la variante.", example="COLLAR-ROJO")
    quantity: int = Field(description="Cantidad vendida.", example=2)
    unit_price: int = Field(description="Precio unitario historico en COP.", example=45000)
    unit_cost: int | None = Field(default=None, description="Costo unitario historico en COP.", example=18000)


class CheckoutAdjustmentOut(BaseModel):
    kind: str = Field(description="Tipo de linea: discount o extra_charge.", example="extra_charge")
    source_type: str | None = Field(default=None, description="Origen funcional de la linea.", example="extra_charge")
    source_id: str | None = Field(default=None, description="Identificador del origen cuando aplica.", example="charge-123")
    name: str = Field(description="Nombre visible de la linea.", example="Empaque para regalo")
    amount: int = Field(description="Monto positivo de la linea en COP.", example=5000)
    code: str | None = Field(default=None, description="Codigo de cupon cuando aplica.", example="VERANO10")


class OrderOut(BaseModel):
    id: str = Field(description="Identificador del pedido.", example="order-123")
    checkout_group_id: str | None = Field(default=None, description="Compra agrupada a la que pertenece el pedido.", example="purchase-123")
    store_id: str = Field(description="Tienda propietaria del pedido.", example="store-123")
    store_name: str = Field(description="Nombre de la tienda.", example="Singular Artesanal")
    buyer_id: str | None = Field(default=None, description="Comprador asociado; nulo para ventas POS anonimas.", example="buyer-123")
    buyer_name: str | None = Field(default=None, description="Nombre del comprador cuando existe.", example="Ana Perez")
    warehouse_id: str | None = Field(default=None, description="Almacen usado para reserva, despacho o venta POS.", example="wh-123")
    address_id: str | None = Field(default=None, description="Direccion de envio; nula para venta presencial.", example="addr-123")
    channel: str = Field(description="Canal de origen del pedido: online o presencial.", pattern="^(online|presencial)$", example="online")
    status: str = Field(description="Estado operativo del pedido.", example="pending")
    subtotal: int = Field(description="Subtotal historico en COP.", example=90000)
    shipping_cost: int = Field(description="Costo de envio en COP.", example=12900)
    tax: int = Field(description="Impuestos registrados en COP.", example=0)
    total: int = Field(description="Total final del pedido en COP.", example=102900)
    notes: str | None = Field(default=None, description="Notas asociadas al pedido.", example="Entregar en porteria")
    created_at: datetime = Field(description="Fecha de creacion del pedido.", example="2026-08-05T10:00:00Z")
    address: AddressOut | None = Field(default=None, description="Direccion historica asociada al pedido.")
    shipping: CheckoutShippingOut | None = Field(default=None, description="Modalidad de envio usada para este pedido.")
    items: list[OrderItemOut] = Field(description="Items historicos del pedido.")
    adjustments: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Descuentos y cargos extra historicos.")
    payments: list[dict] = Field(description="Pagos asociados al pedido.")


class CartOut(BaseModel):
    id: str = Field(description="Identificador del carrito.", example="cart-123")
    items: list[CartItemOut] = Field(description="Items actuales del carrito.")
    store_groups: list[CartStoreGroupOut] = Field(default_factory=list, description="Agrupacion de items por tienda.")
    regular_subtotal: int = Field(default=0, description="Subtotal antes de precios especiales.", example=110000)
    subtotal: int = Field(description="Subtotal despues de precios especiales.", example=95000)
    discount: int = Field(default=0, description="Descuentos estimados del carrito.", example=0)
    extra_charge_total: int = Field(default=0, description="Cargos extra estimados.", example=0)
    shipping_cost: int = Field(description="Costo de envio estimado.", example=12900)
    tax: int = Field(description="Impuestos estimados.", example=0)
    total: int = Field(description="Total estimado.", example=107900)
    checkout_blocked: bool = Field(default=False, description="Indica si algun item bloquea checkout.", example=False)
    blocking_reasons: list[str] = Field(default_factory=list, description="Motivos visibles que bloquean checkout.")


class CheckoutStoreQuoteOut(BaseModel):
    store_id: str = Field(description="Tienda cotizada.", example="store-123")
    store_name: str = Field(description="Nombre publico de la tienda.", example="Nova Ropa")
    items: list[CartItemOut] = Field(description="Items de esta tienda incluidos en la cotizacion.")
    regular_subtotal: int = Field(description="Subtotal regular antes de descuentos.", example=110000)
    subtotal: int = Field(description="Subtotal despues de descuentos.", example=95000)
    discount: int = Field(description="Total descontado por promociones/cupones.", example=15000)
    discounts: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Descuentos aplicados.")
    extra_charge_total: int = Field(description="Total de cargos extra de esta tienda.", example=5000)
    extra_charges: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Cargos extra aplicados.")
    shipping: CheckoutShippingOut = Field(description="Envio calculado para esta tienda.")
    tax: int = Field(description="Impuestos automaticos; permanece en cero.", example=0)
    total: int = Field(description="Total final de esta tienda.", example=112000)
    payment_methods: list[str] = Field(default_factory=list, description="Metodos de pago disponibles para esta tienda.", example=["card", "transfer"])
    payout_accounts: list[dict] = Field(default_factory=list, description="Cuentas manuales disponibles si aplica.")
    contact: CheckoutContactOut | None = Field(default=None, description="Datos publicos de contacto de la tienda.")


class CheckoutQuoteOut(BaseModel):
    subtotal: int = Field(description="Subtotal despues de descuentos.", example=95000)
    regular_subtotal: int = Field(description="Subtotal regular antes de precios especiales.", example=110000)
    discount: int = Field(description="Total descontado.", example=15000)
    discounts: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Descuentos aplicados por promocion o cupon.")
    extra_charge_total: int = Field(description="Total de cargos extra definidos por vendedor.", example=5000)
    extra_charges: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Cargos extra aplicados por separado.")
    shipping_cost: int = Field(description="Costo de envio.", example=12900)
    store_quotes: list[CheckoutStoreQuoteOut] = Field(default_factory=list, description="Desglose independiente por tienda.")
    tax: int = Field(description="Impuestos automaticos de plataforma; permanece en cero porque los cargos son manuales.", example=0)
    total: int = Field(description="Total final.", example=112900)
    currency: str = Field(description="Moneda.", example="COP")


class CheckoutSummaryOut(BaseModel):
    purchase_id: str = Field(description="Identificador de la compra agrupada.", example="purchase-123")
    subtotal: int = Field(description="Subtotal total de la compra.", example=95000)
    discount: int = Field(description="Descuentos totales.", example=15000)
    extra_charge_total: int = Field(description="Cargos extra totales.", example=5000)
    shipping_cost: int = Field(description="Envio total incluido.", example=12900)
    tax: int = Field(description="Impuestos automaticos.", example=0)
    total: int = Field(description="Total final de la compra.", example=112900)
    currency: str = Field(description="Moneda.", example="COP")
    payment_method: str = Field(description="Metodo de pago seleccionado.", example="card")
    address: AddressOut = Field(description="Direccion usada en la compra.")
    store_quotes: list[CheckoutStoreQuoteOut] = Field(description="Resumen por tienda usado al confirmar.")


class CheckoutConfirmationOut(BaseModel):
    purchase_id: str = Field(description="Identificador de la compra agrupada.", example="purchase-123")
    orders: list[OrderOut] = Field(description="Pedidos creados, uno por tienda.")
    summary: CheckoutSummaryOut = Field(description="Resumen completo de la confirmacion.")
    payment_required: bool = Field(description="Indica si queda un pago pendiente.", example=True)
    shipping_notes: list[str] = Field(default_factory=list, description="Notas relevantes de envio para el comprador.")


class PurchaseOut(BaseModel):
    id: str = Field(description="Identificador de la compra agrupada.", example="purchase-123")
    buyer_id: str = Field(description="Comprador propietario de la compra.", example="buyer-123")
    address_id: str | None = Field(default=None, description="Direccion asociada.", example="addr-123")
    subtotal: int = Field(description="Subtotal total.", example=95000)
    discount_total: int = Field(description="Descuentos totales.", example=15000)
    extra_charge_total: int = Field(description="Cargos extra totales.", example=5000)
    shipping_cost: int = Field(description="Costo total de envio incluido.", example=12900)
    tax: int = Field(description="Impuestos automaticos.", example=0)
    total: int = Field(description="Total de la compra.", example=112900)
    currency: str = Field(description="Moneda.", example="COP")
    payment_method: str = Field(description="Metodo de pago seleccionado.", example="card")
    notes: str | None = Field(default=None, description="Notas del comprador.", example="Entregar en porteria")
    created_at: datetime = Field(description="Fecha de creacion.", example="2026-08-05T10:00:00Z")
    orders: list[OrderOut] = Field(description="Pedidos por tienda incluidos en la compra.")
    store_statuses: list[dict] = Field(description="Estado de cada tienda dentro de la compra.")


class PosItemIn(BaseModel):
    variant_id: str = Field(description="Variante propia de la tienda a vender por POS.", example="variant-123")
    quantity: int = Field(description="Cantidad a vender en mostrador.", ge=1, le=1000, example=2)

    model_config = {
        "json_schema_extra": {
            "example": {
                "variant_id": "variant-123",
                "quantity": 2,
            }
        }
    }


class PosOrderIn(BaseModel):
    items: list[PosItemIn] = Field(description="Productos y cantidades vendidos presencialmente.", min_length=1)
    buyer_id: str | None = Field(default=None, description="Comprador opcional si ya existe cuenta; puede omitirse para venta anonima.", example=None)
    payment_method: str = Field(default="cash", description="Metodo de pago presencial informado por el vendedor.", min_length=1, max_length=60, example="cash")
    notes: str | None = Field(default=None, description="Notas internas de la venta presencial.", example="Cliente retira en caja")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "variant_id": "variant-123",
                        "quantity": 2,
                    }
                ],
                "buyer_id": None,
                "payment_method": "cash",
                "notes": "Cliente retira en caja",
            }
        }
    }

