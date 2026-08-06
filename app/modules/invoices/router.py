from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Invoice, Order, Store
from app.models.invoice import InvoiceStatus
from app.models.user import User
from app.modules.common.permissions import get_seller_store, require_buyer
from app.modules.invoices.schemas import InvoiceListItemOut, InvoiceOut
from app.modules.invoices.service import render_invoice_html

buyer_router = APIRouter(tags=["invoices"])
seller_router = APIRouter(prefix="/seller", tags=["seller-invoices"])

BUYER_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol buyer."},
    404: {"description": "Pedido o comprobante no encontrado dentro del scope del comprador."},
    422: {"description": "Validacion Pydantic."},
}

SELLER_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller."},
    404: {"description": "Comprobante no encontrado en la tienda del vendedor."},
    422: {"description": "Validacion Pydantic."},
}


def _invoice_out(invoice: Invoice) -> dict:
    return {
        "id": invoice.id,
        "number": invoice.number,
        "order_id": invoice.order_id,
        "store_id": invoice.store_id,
        "buyer_id": invoice.buyer_id,
        "status": invoice.status.value,
        "currency": invoice.currency,
        "subtotal": invoice.subtotal,
        "discount_total": invoice.discount_total,
        "extra_charge_total": invoice.extra_charge_total,
        "shipping_cost": invoice.shipping_cost,
        "total": invoice.total,
        "shipping_to_convenir": invoice.shipping_to_convenir,
        "issued_at": invoice.issued_at,
        "store_fiscal": invoice.store_fiscal or {},
        "items": invoice.items_snapshot or [],
        "charges": invoice.charges_snapshot or [],
    }


def _buyer_invoice(order_id: str, user: User, db: Session) -> Invoice:
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    invoice = db.scalar(select(Invoice).where(Invoice.order_id == order.id))
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El pedido aun no tiene comprobante emitido")
    return invoice


@buyer_router.get(
    "/orders/{order_id}/invoice",
    response_model=InvoiceOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar comprobante del pedido",
    description=(
        "Rol permitido: buyer. HU-FAC-01. Devuelve el comprobante de venta emitido para un pedido "
        "propio (tras confirmarse el pago), con cargos desglosados y datos fiscales de la tienda."
    ),
    response_description="Comprobante de venta del pedido.",
    responses=BUYER_RESPONSES,
)
def buyer_order_invoice(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return _invoice_out(_buyer_invoice(order_id, user, db))


@buyer_router.get(
    "/orders/{order_id}/invoice/download",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Descargar comprobante del pedido",
    description="Rol permitido: buyer. HU-FAC-01. Devuelve el comprobante como documento HTML autocontenido, imprimible a PDF.",
    response_description="Documento HTML del comprobante.",
    responses=BUYER_RESPONSES,
)
def buyer_order_invoice_download(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return HTMLResponse(render_invoice_html(_buyer_invoice(order_id, user, db)))


@seller_router.get(
    "/invoices",
    response_model=list[InvoiceListItemOut],
    status_code=status.HTTP_200_OK,
    summary="Listar comprobantes de mi tienda",
    description=(
        "Rol permitido: seller. HU-FAC-03. Lista los comprobantes emitidos por la tienda del "
        "vendedor con fecha, comprador, pedido y monto; filtra por rango de fechas y estado del pedido."
    ),
    response_description="Comprobantes emitidos por la tienda.",
    responses={401: SELLER_RESPONSES[401], 403: SELLER_RESPONSES[403], 422: SELLER_RESPONSES[422]},
)
def seller_invoices(
    date_from: date | None = Query(default=None, description="Fecha inicial inclusiva (por emision)."),
    date_to: date | None = Query(default=None, description="Fecha final inclusiva (por emision)."),
    invoice_status: str | None = Query(default=None, alias="status", pattern="^(issued|cancelled|returned)$", description="Estado del comprobante."),
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = select(Invoice).where(Invoice.store_id == store.id)
    if invoice_status:
        stmt = stmt.where(Invoice.status == InvoiceStatus(invoice_status))
    if date_from:
        stmt = stmt.where(Invoice.issued_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
    if date_to:
        stmt = stmt.where(Invoice.issued_at <= datetime.combine(date_to, datetime.max.time(), timezone.utc))
    rows = db.scalars(stmt.order_by(Invoice.issued_at.desc())).all()
    return [
        {
            "id": inv.id,
            "number": inv.number,
            "order_id": inv.order_id,
            "buyer_id": inv.buyer_id,
            "buyer_name": (inv.buyer_snapshot or {}).get("name"),
            "status": inv.status.value,
            "total": inv.total,
            "currency": inv.currency,
            "issued_at": inv.issued_at,
        }
        for inv in rows
    ]


def _seller_invoice(invoice_id: str, store: Store, db: Session) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comprobante no encontrado")
    return invoice


@seller_router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar comprobante de mi tienda",
    description="Rol permitido: seller. HU-FAC-03. Detalle de un comprobante emitido por la tienda del vendedor.",
    response_description="Comprobante de la tienda.",
    responses=SELLER_RESPONSES,
)
def seller_invoice(invoice_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    return _invoice_out(_seller_invoice(invoice_id, store, db))


@seller_router.get(
    "/invoices/{invoice_id}/download",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Descargar comprobante de mi tienda",
    description="Rol permitido: seller. HU-FAC-03. Devuelve el comprobante de la tienda como HTML autocontenido, igual que lo recibe el comprador.",
    response_description="Documento HTML del comprobante.",
    responses=SELLER_RESPONSES,
)
def seller_invoice_download(invoice_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    return HTMLResponse(render_invoice_html(_seller_invoice(invoice_id, store, db)))
