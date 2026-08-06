from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InvoiceItemOut(BaseModel):
    product_name: str = Field(description="Nombre del producto facturado.", example="Collar tejido")
    sku: str | None = Field(default=None, description="SKU de la variante.", example="COLLAR-ROJO")
    quantity: int = Field(description="Cantidad facturada.", example=2)
    unit_price: int = Field(description="Precio unitario en la moneda del comprobante.", example=45000)
    line_total: int = Field(description="Total de la linea (precio x cantidad).", example=90000)


class InvoiceChargeOut(BaseModel):
    kind: str = Field(description="Tipo de linea: discount o extra_charge.", example="extra_charge")
    name: str = Field(description="Nombre visible del cargo o descuento.", example="Empaque para regalo")
    amount: int = Field(description="Monto de la linea.", example=5000)
    source_type: str | None = Field(default=None, description="Origen funcional de la linea.", example="extra_charge")
    code: str | None = Field(default=None, description="Codigo de cupon cuando aplica.", example=None)


class InvoiceStoreFiscalOut(BaseModel):
    name: str | None = Field(default=None, description="Nombre comercial de la tienda.", example="Nova Ropa")
    legal_name: str | None = Field(default=None, description="Razon social/nombre fiscal.", example="Nova Ropa SAS")
    tax_id: str | None = Field(default=None, description="Identificacion tributaria.", example="900123456-7")
    fiscal_address: str | None = Field(default=None, description="Direccion fiscal.", example="Cra 7 # 20-30, Bogota")
    contact_email: str | None = Field(default=None, description="Correo de contacto.", example="tienda@example.com")
    contact_phone: str | None = Field(default=None, description="Telefono de contacto.", example="+573001112233")


class InvoiceOut(BaseModel):
    id: str = Field(description="Identificador del comprobante.", example="inv-123")
    number: int = Field(description="Numero secuencial del comprobante en la tienda.", example=1)
    order_id: str = Field(description="Pedido facturado.", example="order-123")
    store_id: str = Field(description="Tienda emisora.", example="store-123")
    buyer_id: str | None = Field(default=None, description="Comprador.", example="buyer-123")
    status: str = Field(description="Estado del comprobante: issued, cancelled o returned.", example="issued")
    currency: str = Field(description="Moneda.", example="COP")
    subtotal: int = Field(description="Subtotal facturado.", example=90000)
    discount_total: int = Field(description="Descuentos totales.", example=0)
    extra_charge_total: int = Field(description="Cargos extra totales.", example=5000)
    shipping_cost: int = Field(description="Envio facturado (0 si es a convenir).", example=12900)
    total: int = Field(description="Total del comprobante.", example=107900)
    shipping_to_convenir: bool = Field(description="Indica si el envio es a convenir y no se factura.", example=False)
    issued_at: datetime = Field(description="Fecha de emision.", example="2026-08-06T10:00:00Z")
    store_fiscal: InvoiceStoreFiscalOut = Field(description="Datos fiscales de la tienda (snapshot).")
    items: list[InvoiceItemOut] = Field(description="Items facturados (snapshot).")
    charges: list[InvoiceChargeOut] = Field(default_factory=list, description="Descuentos y cargos extra desglosados (snapshot).")


class InvoiceListItemOut(BaseModel):
    id: str = Field(description="Identificador del comprobante.", example="inv-123")
    number: int = Field(description="Numero del comprobante.", example=1)
    order_id: str = Field(description="Pedido facturado.", example="order-123")
    buyer_id: str | None = Field(default=None, description="Comprador.", example="buyer-123")
    buyer_name: str | None = Field(default=None, description="Nombre del comprador (snapshot).", example="Ana Perez")
    status: str = Field(description="Estado del comprobante.", example="issued")
    total: int = Field(description="Total del comprobante.", example=107900)
    currency: str = Field(description="Moneda.", example="COP")
    issued_at: datetime = Field(description="Fecha de emision.", example="2026-08-06T10:00:00Z")
