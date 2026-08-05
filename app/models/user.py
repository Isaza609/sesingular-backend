import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA, Base


class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=UserRole.buyer,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    # Fidelización mostrada en la cuenta del comprador.
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tier: Mapped[str | None] = mapped_column(String(60))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    temporary_password_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store_memberships = relationship("StoreMember", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    orders = relationship("Order", back_populates="buyer")
    cart = relationship("Cart", back_populates="user", uselist=False)
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
