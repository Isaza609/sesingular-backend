from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class AuthUserOut(BaseModel):
    id: str = Field(description="Identificador interno/Supabase del usuario.", example="4c1a3d6e-7f2d-4e9b-9b9a-8e6f2c4a1234")
    email: str = Field(description="Correo electronico del usuario.", pattern=EMAIL_PATTERN, example="comprador@example.com")
    name: str = Field(description="Nombre visible del usuario.", example="Ana Perez")
    phone: str | None = Field(default=None, description="Telefono de contacto.", example="+573001112233")
    role: Literal["buyer", "seller", "admin"] = Field(description="Rol operativo del usuario.", example="buyer")
    active: bool = Field(description="Indica si el usuario puede acceder a la plataforma.", example=True)
    must_change_password: bool = Field(description="Indica si debe cambiar contrasena antes de operar panel.", example=False)
    points: int = Field(description="Puntos de fidelizacion del comprador.", example=0)
    tier: str | None = Field(default=None, description="Nivel de fidelizacion del comprador.", example="bronce")
    created_at: datetime | None = Field(default=None, description="Fecha de creacion del perfil.", example="2026-08-05T10:00:00Z")


class RegisterBuyerIn(BaseModel):
    email: str = Field(description="Correo del comprador que se autorregistra.", pattern=EMAIL_PATTERN, example="comprador@example.com")
    password: str = Field(description="Contrasena inicial del comprador.", min_length=8, example="CompraSegura123")
    name: str = Field(description="Nombre completo del comprador.", min_length=1, max_length=200, example="Ana Perez")
    phone: str | None = Field(default=None, description="Telefono de contacto opcional.", max_length=40, example="+573001112233")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "comprador@example.com",
                "password": "CompraSegura123",
                "name": "Ana Perez",
                "phone": "+573001112233",
            }
        }
    )


class LoginIn(BaseModel):
    email: str = Field(description="Correo registrado.", pattern=EMAIL_PATTERN, example="comprador@example.com")
    password: str = Field(description="Contrasena del usuario.", min_length=1, example="CompraSegura123")

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "comprador@example.com", "password": "CompraSegura123"}}
    )


class SessionOut(BaseModel):
    user: AuthUserOut = Field(description="Perfil local autenticado.")
    access_token: str | None = Field(default=None, description="JWT emitido por Supabase Auth.", example="eyJhbGciOi...")
    refresh_token: str | None = Field(default=None, description="Token para refrescar la sesion.", example="refresh-token")
    token_type: str = Field(description="Tipo de token retornado.", example="bearer")
    status: Literal["authenticated", "pending_confirmation"] = Field(description="Estado de la sesion.", example="authenticated")
    must_change_password: bool = Field(description="Atajo para indicar cambio obligatorio de contrasena.", example=False)


class ProfilePatch(BaseModel):
    name: str | None = Field(default=None, description="Nombre completo actualizado.", min_length=1, max_length=200, example="Ana Maria Perez")
    phone: str | None = Field(default=None, description="Telefono actualizado.", max_length=40, example="+573004445566")

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Ana Maria Perez", "phone": "+573004445566"}})


class PasswordChangeIn(BaseModel):
    new_password: str = Field(description="Nueva contrasena que cumple la politica minima.", min_length=8, example="NuevaClave123")

    model_config = ConfigDict(json_schema_extra={"example": {"new_password": "NuevaClave123"}})


class PasswordRecoveryRequestIn(BaseModel):
    email: str = Field(description="Correo registrado que recibira enlace o codigo.", pattern=EMAIL_PATTERN, example="vendedor@example.com")

    model_config = ConfigDict(json_schema_extra={"example": {"email": "vendedor@example.com"}})


class PasswordRecoveryConfirmIn(BaseModel):
    recovery_token: str = Field(description="Token/codigo vigente emitido por Supabase Auth.", min_length=1, example="recovery-token")
    new_password: str = Field(description="Nueva contrasena que cumple la politica minima.", min_length=8, example="NuevaClave123")
    email: str | None = Field(default=None, description="Correo asociado, si el proveedor lo requiere.", pattern=EMAIL_PATTERN, example="vendedor@example.com")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recovery_token": "recovery-token",
                "new_password": "NuevaClave123",
                "email": "vendedor@example.com",
            }
        }
    )


class MessageOut(BaseModel):
    message: str = Field(description="Mensaje funcional de la operacion.", example="Solicitud recibida")
