import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SCHEMA


class ShipmentStatus(str, enum.Enum):
    pending = "pending"
    in_transit = "in_transit"
    delivered = "delivered"
    returned = "returned"


# Etiquetas de seguimiento que el vendedor puede fijar manualmente (HU-ENV-05). Se guardan
# como texto en ShipmentEvent y se mapean al enum coarse de Shipment para el estado vigente.
SHIPMENT_TRACKING_STATUSES = ("preparing", "shipped", "in_transit", "delivered", "returned")

_TRACKING_TO_SHIPMENT = {
    "preparing": ShipmentStatus.pending,
    "shipped": ShipmentStatus.in_transit,
    "in_transit": ShipmentStatus.in_transit,
    "delivered": ShipmentStatus.delivered,
    "returned": ShipmentStatus.returned,
}


def tracking_to_shipment_status(label: str) -> ShipmentStatus:
    return _TRACKING_TO_SHIPMENT.get(label, ShipmentStatus.pending)


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    carrier: Mapped[str | None] = mapped_column(String(120))
    tracking_number: Mapped[str | None] = mapped_column(String(120), index=True)
    tracking_url: Mapped[str | None] = mapped_column(String(500))
    cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, name="shipment_status", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=ShipmentStatus.pending,
    )
    # Etiqueta de seguimiento vigente (HU-ENV-05); el enum `status` guarda la versión coarse.
    tracking_status: Mapped[str | None] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(Text)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order = relationship("Order", back_populates="shipments")
    events = relationship(
        "ShipmentEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="ShipmentEvent.created_at",
    )


class ShipmentEvent(Base):
    """Línea de tiempo del envío (HU-ENV-05): cada actualización manual del vendedor.

    Es de solo lectura para el comprador; conserva estado, nota/referencia y fecha.
    """

    __tablename__ = "shipment_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # preparing|shipped|in_transit|delivered|returned
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    shipment = relationship("Shipment", back_populates="events")
