import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SCHEMA


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    returned = "returned"


class SaleChannel(str, enum.Enum):
    online = "online"
    presencial = "presencial"


class OrderAdjustmentKind(str, enum.Enum):
    discount = "discount"
    extra_charge = "extra_charge"


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(80))
    recipient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    address_line: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="addresses")


class CheckoutGroup(Base):
    __tablename__ = "checkout_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    buyer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.addresses.id", ondelete="SET NULL"), index=True
    )
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extra_charge_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shipping_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tax: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    payment_method: Mapped[str] = mapped_column(String(60), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    buyer = relationship("User")
    address = relationship("Address")
    orders = relationship("Order", back_populates="checkout_group")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checkout_group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.checkout_groups.id", ondelete="SET NULL"), index=True
    )
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable: ventas POS sin comprador registrado
    buyer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"), index=True
    )
    # Nullable: se asigna después si la tienda tiene más de un almacén
    warehouse_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.warehouses.id", ondelete="SET NULL"), index=True
    )
    address_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.addresses.id", ondelete="SET NULL")
    )
    channel: Mapped[SaleChannel] = mapped_column(
        Enum(SaleChannel, name="sale_channel", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=SaleChannel.online,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=OrderStatus.pending,
        index=True,
    )
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shipping_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tax: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    # Responsable del pedido dentro del equipo de la tienda (HU-PED-05). Nullable: los
    # pedidos llegan "sin asignar" y cualquier miembro puede tomarlos o reasignarlos.
    assignee_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"), index=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Motivo registrado al anular el pedido (HU-PED-04).
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    checkout_group = relationship("CheckoutGroup", back_populates="orders")
    store = relationship("Store", back_populates="orders")
    buyer = relationship("User", back_populates="orders", foreign_keys=[buyer_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    warehouse = relationship("Warehouse")
    address = relationship("Address")
    items = relationship("OrderItem", back_populates="order")
    adjustments = relationship("OrderAdjustment", back_populates="order")
    payments = relationship("Payment", back_populates="order")
    shipments = relationship("Shipment", back_populates="order")
    assignment_events = relationship(
        "OrderAssignmentEvent",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderAssignmentEvent.created_at",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.product_variants.id", ondelete="SET NULL"), index=True
    )
    # Denormalizados: el histórico del pedido no cambia si el producto se edita/elimina
    product_name: Mapped[str] = mapped_column(String(300), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(80))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[int | None] = mapped_column(Integer)

    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")


class OrderAdjustment(Base):
    __tablename__ = "order_adjustments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[OrderAdjustmentKind] = mapped_column(
        Enum(OrderAdjustmentKind, name="order_adjustment_kind", schema=SCHEMA, native_enum=True),
        nullable=False,
    )
    source_type: Mapped[str | None] = mapped_column(String(40))
    source_id: Mapped[str | None] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="adjustments")


class OrderAssignmentEvent(Base):
    """Historial de reasignaciones del responsable de un pedido (HU-PED-05)."""

    __tablename__ = "order_assignment_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_user_id: Mapped[str | None] = mapped_column(String(36))
    to_user_id: Mapped[str | None] = mapped_column(String(36))
    actor_user_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="assignment_events")
