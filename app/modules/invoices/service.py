"""Emisión y render del comprobante de venta al comprador (Épica 11).

El comprobante se emite al confirmarse el pago y toma snapshots de los datos fiscales de
la tienda, del comprador, de los items y de los cargos, de modo que correcciones o
ediciones posteriores no alteren el documento ya emitido (HU-FAC-01/02).
"""

from __future__ import annotations

import html

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Invoice, Order
from app.models.invoice import InvoiceStatus
from app.models.order import OrderAdjustmentKind, OrderStatus


def _store_fiscal_snapshot(store) -> dict:
    return {
        "store_id": store.id,
        "name": store.name,
        "legal_name": store.legal_name or store.name,
        "tax_id": store.tax_id,
        "fiscal_address": store.fiscal_address,
        "contact_email": store.contact_email,
        "contact_phone": store.contact_phone,
    }


def _buyer_snapshot(order: Order) -> dict:
    buyer = order.buyer
    address = order.address
    return {
        "buyer_id": order.buyer_id,
        "name": buyer.name if buyer else None,
        "email": buyer.email if buyer else None,
        "address": (
            {
                "recipient_name": address.recipient_name,
                "address_line": address.address_line,
                "city": address.city,
                "region": address.region,
                "phone": address.phone,
            }
            if address
            else None
        ),
    }


def issue_invoice(db: Session, order: Order) -> Invoice:
    """Emite el comprobante del pedido (idempotente por pedido)."""
    existing = db.scalar(select(Invoice).where(Invoice.order_id == order.id))
    if existing is not None:
        return existing

    from app.modules.catalog.router import get_store_settings_value  # import diferido: evita ciclo

    store = order.store
    last_number = db.scalar(select(func.max(Invoice.number)).where(Invoice.store_id == store.id))
    number = (last_number or 0) + 1

    charges: list[dict] = []
    discount_total = 0
    extra_charge_total = 0
    for adj in order.adjustments:
        charges.append(
            {
                "kind": adj.kind.value,
                "name": adj.name,
                "amount": adj.amount,
                "source_type": adj.source_type,
                "code": (adj.metadata_json or {}).get("code"),
            }
        )
        if adj.kind == OrderAdjustmentKind.extra_charge:
            extra_charge_total += adj.amount
        elif adj.kind == OrderAdjustmentKind.discount:
            discount_total += adj.amount

    items_snapshot = [
        {
            "product_name": item.product_name,
            "sku": item.sku,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "line_total": item.unit_price * item.quantity,
        }
        for item in order.items
    ]

    settings = get_store_settings_value(store.id, db)
    shipping_to_convenir = order.shipping_cost == 0 and getattr(settings, "shipping_mode", None) == "to_agree"

    invoice = Invoice(
        number=number,
        order_id=order.id,
        store_id=store.id,
        buyer_id=order.buyer_id,
        status=_status_for_order(order),
        currency="COP",
        subtotal=order.subtotal,
        discount_total=discount_total,
        extra_charge_total=extra_charge_total,
        shipping_cost=0 if shipping_to_convenir else order.shipping_cost,
        total=order.total,
        shipping_to_convenir=shipping_to_convenir,
        store_fiscal=_store_fiscal_snapshot(store),
        buyer_snapshot=_buyer_snapshot(order),
        items_snapshot=items_snapshot,
        charges_snapshot=charges,
    )
    db.add(invoice)
    db.flush()
    return invoice


def _status_for_order(order: Order) -> InvoiceStatus:
    if order.status == OrderStatus.cancelled:
        return InvoiceStatus.cancelled
    if order.status == OrderStatus.returned:
        return InvoiceStatus.returned
    return InvoiceStatus.issued


def sync_invoice_status(db: Session, order: Order) -> None:
    """Refleja en el comprobante que el pedido fue cancelado o devuelto (HU-FAC-01)."""
    invoice = db.scalar(select(Invoice).where(Invoice.order_id == order.id))
    if invoice is None:
        return
    invoice.status = _status_for_order(order)


def _money(value: int, currency: str = "COP") -> str:
    return f"${value:,.0f} {currency}".replace(",", ".")


def render_invoice_html(invoice: Invoice) -> str:
    """Documento HTML autocontenido (imprimible a PDF por el navegador)."""
    fiscal = invoice.store_fiscal or {}
    buyer = invoice.buyer_snapshot or {}
    address = buyer.get("address") or {}

    def esc(value) -> str:
        return html.escape(str(value)) if value is not None else ""

    rows = "".join(
        "<tr>"
        f"<td>{esc(item.get('product_name'))}</td>"
        f"<td>{esc(item.get('sku') or '')}</td>"
        f"<td style='text-align:right'>{esc(item.get('quantity'))}</td>"
        f"<td style='text-align:right'>{_money(item.get('unit_price', 0), invoice.currency)}</td>"
        f"<td style='text-align:right'>{_money(item.get('line_total', 0), invoice.currency)}</td>"
        "</tr>"
        for item in (invoice.items_snapshot or [])
    )

    charge_lines = "".join(
        "<tr>"
        f"<td colspan='4' style='text-align:right'>{esc(charge.get('name'))}"
        f"{' (descuento)' if charge.get('kind') == 'discount' else ''}</td>"
        f"<td style='text-align:right'>{'-' if charge.get('kind') == 'discount' else ''}"
        f"{_money(charge.get('amount', 0), invoice.currency)}</td>"
        "</tr>"
        for charge in (invoice.charges_snapshot or [])
    )

    if invoice.shipping_to_convenir:
        shipping_line = (
            "<tr><td colspan='4' style='text-align:right'>Envío</td>"
            "<td style='text-align:right'>A convenir con el vendedor (no facturado)</td></tr>"
        )
    else:
        shipping_line = (
            "<tr><td colspan='4' style='text-align:right'>Envío</td>"
            f"<td style='text-align:right'>{_money(invoice.shipping_cost, invoice.currency)}</td></tr>"
        )

    status_labels = {"issued": "Emitido", "cancelled": "Anulado", "returned": "Devuelto"}
    status_banner = ""
    if invoice.status.value != "issued":
        status_banner = f"<p style='color:#b00;font-weight:bold'>Estado: {status_labels.get(invoice.status.value)}</p>"

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Comprobante {esc(invoice.number)} - {esc(fiscal.get('legal_name'))}</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#222;max-width:720px;margin:24px auto;padding:0 16px}}
h1{{font-size:20px;margin:0 0 4px}} .muted{{color:#666;font-size:13px}}
table{{width:100%;border-collapse:collapse;margin-top:16px}}
th,td{{padding:8px;border-bottom:1px solid #eee;font-size:14px}} th{{text-align:left;background:#fafafa}}
.total{{font-size:18px;font-weight:bold}}
</style></head><body>
<h1>{esc(fiscal.get('legal_name'))}</h1>
<p class="muted">
NIT/ID: {esc(fiscal.get('tax_id') or 'N/D')} · {esc(fiscal.get('fiscal_address') or '')}<br>
{esc(fiscal.get('contact_email') or '')} · {esc(fiscal.get('contact_phone') or '')}
</p>
<hr>
<p><b>Comprobante N°:</b> {esc(invoice.number)} &nbsp; <b>Pedido:</b> {esc(invoice.order_id)}<br>
<b>Fecha:</b> {esc(invoice.issued_at)}</p>
{status_banner}
<p><b>Comprador:</b> {esc(buyer.get('name') or 'N/D')} ({esc(buyer.get('email') or '')})<br>
{esc(address.get('address_line') or '')} {esc(address.get('city') or '')} {esc(address.get('region') or '')}</p>
<table>
<thead><tr><th>Producto</th><th>SKU</th><th style="text-align:right">Cant.</th><th style="text-align:right">Precio</th><th style="text-align:right">Total</th></tr></thead>
<tbody>
{rows}
<tr><td colspan="4" style="text-align:right">Subtotal</td><td style="text-align:right">{_money(invoice.subtotal, invoice.currency)}</td></tr>
{charge_lines}
{shipping_line}
<tr><td colspan="4" style="text-align:right" class="total">Total</td><td style="text-align:right" class="total">{_money(invoice.total, invoice.currency)}</td></tr>
</tbody></table>
<p class="muted">Este documento es el comprobante de la venta entre el vendedor y el comprador. La plataforma no calcula impuestos.</p>
</body></html>"""
