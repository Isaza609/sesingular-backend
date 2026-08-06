from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentIntentOut(BaseModel):
    payment_id: str = Field(description="Identificador del pago creado o reutilizado.", example="pay-123")
    order_id: str = Field(description="Pedido asociado al intento de pago.", example="order-123")
    provider: str = Field(description="Proveedor de pasarela configurado en la plataforma.", example="mercadopago")
    status: str = Field(description="Estado actual del pago.", example="pending")
    amount: int = Field(description="Monto a cobrar por la pasarela.", example=110000)
    currency: str = Field(description="Moneda del cobro.", example="COP")
    checkout_url: str | None = Field(default=None, description="URL de checkout de la pasarela si aplica.", example=None)

    model_config = {
        "json_schema_extra": {
            "example": {
                "payment_id": "pay-123",
                "order_id": "order-123",
                "provider": "mercadopago",
                "status": "pending",
                "amount": 110000,
                "currency": "COP",
                "checkout_url": None,
            }
        }
    }


class WebhookIn(BaseModel):
    provider_payment_id: str | None = Field(default=None, description="Identificador del pago en la pasarela.", example="mp-987")
    order_id: str | None = Field(default=None, description="Pedido asociado si la pasarela no envia provider_payment_id.", example="order-123")
    status: str | None = Field(default=None, description="Estado reportado: approved, paid, rejected, refunded, pending.", example="approved")
    data: dict | None = Field(default=None, description="Carga cruda alterna de la pasarela (data.id, data.status).", example={"id": "mp-987", "status": "approved"})

    model_config = {
        "json_schema_extra": {
            "example": {
                "provider_payment_id": "mp-987",
                "order_id": "order-123",
                "status": "approved",
            }
        }
    }


class WebhookResultOut(BaseModel):
    payment_id: str = Field(description="Pago afectado por la notificacion.", example="pay-123")
    order_id: str = Field(description="Pedido asociado.", example="order-123")
    status: str = Field(description="Nuevo estado del pago tras el webhook.", example="paid")
