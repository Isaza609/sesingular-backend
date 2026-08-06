import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA, Base


class InvoiceStatus(str, enum.Enum):
    issued = "issued"        # emitido
    cancelled = "cancelled"  # el pedido fue anulado
    returned = "returned"    # el pedido fue devuelto


class Invoice(Base):
    """Comprobante de venta al comprador (Épica 11).

    Se emite al confirmarse el pago (`pago_confirmado`). Guarda snapshots de los datos
    fiscales de la tienda, del comprador, de los items y de los cargos, de modo que una
    corrección posterior (HU-FAC-02) o una edición del pedido no altere el documento ya
    emitido. Un comprobante por pedido (idempotente por `order_id`).
    """

    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    number: Mapped[int] = mapped_column(Integer, nullable=False)  # secuencial por tienda
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    buyer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=InvoiceStatus.issued,
        index=True,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extra_charge_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shipping_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # True cuando el envío es "a convenir": no se factura y se acuerda por fuera (HU-FAC-01).
    shipping_to_convenir: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Snapshots tomados al emitir (JSON): datos fiscales de la tienda, comprador, items y cargos.
    store_fiscal: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    buyer_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    items_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    charges_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order")
    store = relationship("Store")
    buyer = relationship("User")
