"""Notificaciones por correo (RF-PAGO-06) usando Resend.

El envío nunca debe romper el flujo de pago: si falta la API key o el proveedor
falla, se registra y se sigue. Llamar siempre vía BackgroundTasks.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"


def email_enabled() -> bool:
    settings = get_settings()
    return bool(settings.resend_api_key and settings.email_from)


def send_email(to: str | None, subject: str, html: str) -> None:
    """Envía un correo. No lanza excepciones: sólo registra los fallos."""
    if not to or not email_enabled():
        logger.info("Correo omitido (sin destinatario o proveedor sin configurar): %s", subject)
        return
    settings = get_settings()
    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": settings.email_from, "to": [to], "subject": subject, "html": html},
            )
        if response.status_code >= 400:
            logger.warning("Resend devolvió %s: %s", response.status_code, response.text)
    except httpx.HTTPError as exc:
        logger.warning("No se pudo enviar el correo '%s': %s", subject, exc)


def _layout(title: str, body: str) -> str:
    return (
        '<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:520px;margin:0 auto">'
        f'<h2 style="color:#0045E0;margin-bottom:8px">{title}</h2>'
        f'<div style="color:#333;line-height:1.6">{body}</div>'
        '<p style="color:#999;font-size:12px;margin-top:24px">Singular · Accesorios hechos a mano</p>'
        "</div>"
    )


def receipt_uploaded_to_seller(to: str | None, order_id: str, buyer_name: str, amount_text: str) -> None:
    send_email(
        to,
        f"Nuevo comprobante por revisar · Pedido {order_id}",
        _layout(
            "Tienes un comprobante pendiente",
            f"<p><b>{buyer_name}</b> subió el comprobante del pedido <b>{order_id}</b> por <b>{amount_text}</b>.</p>"
            "<p>Entra a tu panel, sección <b>Pagos</b>, para revisarlo y confirmar si el dinero llegó.</p>",
        ),
    )


def receipt_uploaded_to_buyer(to: str | None, order_id: str) -> None:
    send_email(
        to,
        f"Recibimos tu comprobante · Pedido {order_id}",
        _layout(
            "Comprobante recibido",
            f"<p>Recibimos el comprobante de tu pedido <b>{order_id}</b>.</p>"
            "<p>El vendedor lo va a verificar y te avisamos apenas confirme el pago.</p>",
        ),
    )


def payment_confirmed_to_buyer(to: str | None, order_id: str, amount_text: str) -> None:
    send_email(
        to,
        f"¡Pago confirmado! · Pedido {order_id}",
        _layout(
            "Tu pago fue confirmado 🎉",
            f"<p>El vendedor confirmó el pago de <b>{amount_text}</b> para el pedido <b>{order_id}</b>.</p>"
            "<p>Ya estamos preparando tu pedido.</p>",
        ),
    )


def payment_rejected_to_buyer(to: str | None, order_id: str, note: str | None) -> None:
    reason = f"<p><b>Motivo:</b> {note}</p>" if note else ""
    send_email(
        to,
        f"No pudimos verificar tu pago · Pedido {order_id}",
        _layout(
            "Pago no verificado",
            f"<p>El vendedor no pudo verificar el pago del pedido <b>{order_id}</b>.</p>"
            f"{reason}"
            "<p>Puedes subir un comprobante nuevo desde tu cuenta o contactar al vendedor.</p>",
        ),
    )


def checkout_summary_to_buyer(to: str | None, confirmation: dict) -> None:
    summary = confirmation.get("summary", {})
    store_quotes = summary.get("store_quotes", [])
    orders = confirmation.get("orders", [])
    total = f"${summary.get('total', 0):,.0f} COP".replace(",", ".")
    rows = "".join(
        (
            "<li>"
            f"<b>{quote.get('store_name')}</b>: "
            f"{len(quote.get('items', []))} item(s), total "
            f"${quote.get('total', 0):,.0f} COP"
            f" · envio: {quote.get('shipping', {}).get('label') or 'configurado'}"
            "</li>"
        )
        for quote in store_quotes
    )
    order_ids = ", ".join(
        order.get("id", "") if isinstance(order, dict) else getattr(order, "id", "")
        for order in orders
    )
    notes = "".join(f"<p><b>Nota de envio:</b> {note}</p>" for note in confirmation.get("shipping_notes", []))
    send_email(
        to,
        f"Resumen de tu compra · {confirmation.get('purchase_id')}",
        _layout(
            "Compra confirmada",
            f"<p>Confirmamos tu compra <b>{confirmation.get('purchase_id')}</b>.</p>"
            f"<p><b>Pedidos:</b> {order_ids}</p>"
            f"<p><b>Total:</b> {total}</p>"
            f"<p><b>Metodo de pago:</b> {summary.get('payment_method')}</p>"
            f"<ul>{rows}</ul>"
            f"{notes}",
        ),
    )
