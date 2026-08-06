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


ORDER_STATUS_LABELS = {
    "pending": "pendiente",
    "confirmed": "confirmado",
    "preparing": "en preparación",
    "shipped": "enviado",
    "delivered": "entregado",
    "cancelled": "cancelado",
    "returned": "devuelto",
}


def order_status_changed_to_buyer(to: str | None, order_id: str, new_status: str) -> None:
    """HU-PED-02: aviso al comprador del nuevo estado del pedido."""
    label = ORDER_STATUS_LABELS.get(new_status, new_status)
    send_email(
        to,
        f"Tu pedido {order_id} ahora está {label}",
        _layout(
            "Actualización de tu pedido",
            f"<p>El estado de tu pedido <b>{order_id}</b> cambió a <b>{label}</b>.</p>"
            "<p>Puedes ver el detalle y el seguimiento desde tu cuenta.</p>",
        ),
    )


def order_status_changed_to_seller(to: str | None, order_id: str, new_status: str) -> None:
    """HU-PED-02: aviso al vendedor del nuevo estado del pedido."""
    label = ORDER_STATUS_LABELS.get(new_status, new_status)
    send_email(
        to,
        f"Pedido {order_id}: {label}",
        _layout(
            "Actualización de pedido",
            f"<p>El pedido <b>{order_id}</b> de tu tienda cambió a <b>{label}</b>.</p>",
        ),
    )


SHIPMENT_STATUS_LABELS = {
    "preparing": "en preparación",
    "shipped": "despachado",
    "in_transit": "en camino",
    "delivered": "entregado",
    "returned": "devuelto",
}


def shipment_status_to_buyer(to: str | None, order_id: str, new_status: str, note: str | None) -> None:
    """HU-ENV-05: aviso al comprador del nuevo estado de envío con la nota del vendedor."""
    label = SHIPMENT_STATUS_LABELS.get(new_status, new_status)
    detail = f"<p><b>Nota del vendedor:</b> {note}</p>" if note else ""
    send_email(
        to,
        f"Envío de tu pedido {order_id}: {label}",
        _layout(
            "Seguimiento de tu envío",
            f"<p>El envío de tu pedido <b>{order_id}</b> ahora está <b>{label}</b>.</p>{detail}"
            "<p>Consulta la línea de tiempo desde el detalle de tu pedido.</p>",
        ),
    )


def order_cancelled_to_buyer(to: str | None, order_id: str, reason: str | None) -> None:
    """HU-PED-04: aviso al comprador de la anulación del pedido con su motivo."""
    detail = f"<p><b>Motivo:</b> {reason}</p>" if reason else ""
    send_email(
        to,
        f"Tu pedido {order_id} fue cancelado",
        _layout(
            "Pedido cancelado",
            f"<p>El vendedor anuló tu pedido <b>{order_id}</b>.</p>{detail}"
            "<p>Si ya habías pagado, contacta al vendedor para resolver el caso.</p>",
        ),
    )


def _money(value: int) -> str:
    return f"${value:,.0f} COP".replace(",", ".")


def payment_incomplete_to_buyer(
    to: str | None,
    order_id: str,
    expected_amount: int,
    received_amount: int,
    difference: int,
    account: dict | None,
) -> None:
    """HU-PAG-07/08: aviso al comprador de que falto dinero y debe subir el saldo."""
    if account:
        if account.get("type") == "bre_b":
            destino = f"<p><b>Llave Bre-B:</b> {account.get('breb_key')} · <b>Titular:</b> {account.get('holder_name')}</p>"
        else:
            destino = (
                f"<p><b>Banco:</b> {account.get('bank_name')} · <b>Cuenta:</b> {account.get('account_type')} "
                f"{account.get('account_number')} · <b>Titular:</b> {account.get('holder_name')}</p>"
            )
    else:
        destino = ""
    send_email(
        to,
        f"Falta completar tu pago · Pedido {order_id}",
        _layout(
            "Tu pago quedó incompleto",
            f"<p>El vendedor recibió un monto menor al total del pedido <b>{order_id}</b>.</p>"
            f"<p><b>Esperado:</b> {_money(expected_amount)}<br>"
            f"<b>Recibido:</b> {_money(received_amount)}<br>"
            f"<b>Diferencia pendiente:</b> {_money(difference)}</p>"
            f"{destino}"
            "<p>Transfiere el saldo faltante y vuelve a subir el comprobante desde el detalle de tu pedido.</p>",
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
