import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA, Base


class PayoutAccountType(str, enum.Enum):
    """Medio de cobro manual del vendedor (comparten el mismo flujo)."""

    bank = "bank"
    bre_b = "bre_b"


class PayoutAccount(Base):
    """Cuenta de cobro manual de una tienda (transferencia bancaria o Bre-B).

    Las cuentas pertenecen al vendedor, no a la plataforma. Se desactivan en vez de
    borrarse para conservar la referencia en pedidos ya pagados.
    """

    __tablename__ = "payout_accounts"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[PayoutAccountType] = mapped_column(
        Enum(PayoutAccountType, name="payout_account_type", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=PayoutAccountType.bank,
    )
    label: Mapped[str | None] = mapped_column(String(120))
    # Transferencia bancaria
    bank_name: Mapped[str | None] = mapped_column(String(120))
    account_type: Mapped[str | None] = mapped_column(String(40))  # ahorros | corriente
    account_number: Mapped[str | None] = mapped_column(String(60))
    # Bre-B
    breb_key: Mapped[str | None] = mapped_column(String(120))
    # Titular (común a ambos)
    holder_name: Mapped[str] = mapped_column(String(200), nullable=False)
    holder_document: Mapped[str | None] = mapped_column(String(40))

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store = relationship("Store")
