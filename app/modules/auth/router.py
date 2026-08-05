from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.models.user import UserRole
from app.modules.auth.deps import get_current_user
from app.modules.auth.schemas import (
    AuthUserOut,
    LoginIn,
    MessageOut,
    PasswordChangeIn,
    PasswordRecoveryConfirmIn,
    PasswordRecoveryRequestIn,
    ProfilePatch,
    RegisterBuyerIn,
    SessionOut,
)
from app.modules.auth.service import AuthServiceError, SupabaseAuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

ERRORS_AUTH_PUBLIC = {
    400: {"description": "Datos invalidos o regla de negocio violada."},
    401: {"description": "Credenciales invalidas."},
    403: {"description": "Usuario inactivo, credencial temporal vencida o cambio obligatorio pendiente."},
    409: {"description": "El correo ya existe."},
    422: {"description": "Validacion Pydantic."},
    502: {"description": "Supabase Auth no disponible o no configurado."},
}

ERRORS_AUTH_PRIVATE = {
    400: {"description": "Datos invalidos o regla de negocio violada."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Usuario inactivo o cambio obligatorio pendiente."},
    422: {"description": "Validacion Pydantic."},
    502: {"description": "Supabase Auth no disponible o no configurado."},
}


def _user_out(user: User) -> AuthUserOut:
    return AuthUserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role.value,
        active=user.active,
        must_change_password=user.must_change_password,
        points=user.points,
        tier=user.tier,
        created_at=user.created_at,
    )


def _auth_error(exc: AuthServiceError, generic_credentials: bool = False) -> HTTPException:
    if generic_credentials and exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return HTTPException(exc.status_code, exc.message)


def _auth_user_id(data: dict, fallback: str | None = None) -> str:
    user = data.get("user") or data
    return str(user.get("id") or user.get("sub") or fallback or "")


def _session_out(user: User, auth_data: dict, status_label: str = "authenticated") -> SessionOut:
    return SessionOut(
        user=_user_out(user),
        access_token=auth_data.get("access_token"),
        refresh_token=auth_data.get("refresh_token"),
        token_type=auth_data.get("token_type") or "bearer",
        status=status_label,
        must_change_password=user.must_change_password,
    )


@router.post(
    "/register",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar comprador",
    description=(
        "Rol permitido: publico. HU-USR-01. Registra exclusivamente compradores; "
        "vendedores y administradores solo se crean desde administracion."
    ),
    response_description="Sesion o estado de confirmacion del comprador creado.",
    responses=ERRORS_AUTH_PUBLIC,
)
def register_buyer(
    body: RegisterBuyerIn,
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> SessionOut:
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya esta registrado")
    try:
        auth_data = auth.sign_up_buyer(body.email, body.password, {"name": body.name, "full_name": body.name})
    except AuthServiceError as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya esta registrado") from exc
        raise _auth_error(exc) from exc

    user_id = _auth_user_id(auth_data)
    if not user_id:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Supabase Auth no retorno identificador de usuario")
    user = User(id=user_id, email=body.email, name=body.name, phone=body.phone, role=UserRole.buyer)
    db.add(user)
    db.commit()
    db.refresh(user)
    status_label = "authenticated" if auth_data.get("access_token") else "pending_confirmation"
    return _session_out(user, auth_data, status_label)


@router.post(
    "/login",
    response_model=SessionOut,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesion",
    description=(
        "Rol permitido: publico. HU-USR-01 y HU-USR-02. Autentica con Supabase Auth, "
        "rechaza credenciales invalidas sin revelar cual dato fallo y senala cambio obligatorio."
    ),
    response_description="Sesion autenticada con perfil local y bandera de cambio obligatorio.",
    responses=ERRORS_AUTH_PUBLIC,
)
def login(
    body: LoginIn,
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> SessionOut:
    try:
        auth_data = auth.sign_in_with_password(body.email, body.password)
    except AuthServiceError as exc:
        raise _auth_error(exc, generic_credentials=True) from exc

    user_id = _auth_user_id(auth_data)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        user = db.scalar(select(User).where(User.email == body.email))
    if user is None:
        user = User(id=user_id or body.email, email=body.email, name=body.email.split("@")[0], role=UserRole.buyer)
        db.add(user)
        db.flush()
    if not user.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario desactivado")
    if user.must_change_password and user.temporary_password_expires_at:
        expires_at = user.temporary_password_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Credencial temporal expirada; contacta al administrador")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return _session_out(user, auth_data)


@router.get(
    "/me",
    response_model=AuthUserOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil",
    description="Rol permitido: buyer, seller, admin. HU-USR-03. Retorna el perfil del usuario autenticado.",
    response_description="Perfil del usuario autenticado.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Usuario desactivado."}},
)
def me(user: User = Depends(get_current_user)) -> AuthUserOut:
    return _user_out(user)


@router.patch(
    "/me",
    response_model=AuthUserOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil",
    description="Rol permitido: buyer, seller, admin. HU-USR-03. Actualiza nombre y telefono del usuario autenticado.",
    response_description="Perfil actualizado.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Usuario desactivado."}, 422: {"description": "Validacion Pydantic."}},
)
def patch_me(
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthUserOut:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post(
    "/change-password",
    response_model=AuthUserOut,
    status_code=status.HTTP_200_OK,
    summary="Cambiar contrasena",
    description=(
        "Rol permitido: buyer, seller, admin. HU-USR-02 y HU-USR-04. Cambia la contrasena "
        "del usuario autenticado y libera el bloqueo de primer ingreso cuando aplica."
    ),
    response_description="Perfil actualizado sin cambio obligatorio pendiente.",
    responses=ERRORS_AUTH_PRIVATE,
)
def change_password(
    body: PasswordChangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> AuthUserOut:
    try:
        auth.admin_update_user_password(user.id, body.new_password)
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc
    user.must_change_password = False
    user.temporary_password_expires_at = None
    user.password_changed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post(
    "/password-recovery/request",
    response_model=MessageOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar recuperacion",
    description=(
        "Rol permitido: publico. HU-USR-04. Solicita enlace o codigo de recuperacion por correo "
        "sin devolver tokens ni secretos."
    ),
    response_description="Confirmacion de recepcion de la solicitud.",
    responses=ERRORS_AUTH_PUBLIC,
)
def request_password_recovery(
    body: PasswordRecoveryRequestIn,
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> MessageOut:
    try:
        auth.send_password_recovery(body.email)
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc
    return MessageOut(message="Si el correo esta registrado, recibira instrucciones para restablecer la contrasena")


@router.post(
    "/password-recovery/confirm",
    response_model=MessageOut,
    status_code=status.HTTP_200_OK,
    summary="Confirmar recuperacion",
    description=(
        "Rol permitido: publico. HU-USR-04. Usa un token o codigo vigente de recuperacion "
        "para definir una nueva contrasena."
    ),
    response_description="Confirmacion del cambio de contrasena.",
    responses=ERRORS_AUTH_PUBLIC,
)
def confirm_password_recovery(
    body: PasswordRecoveryConfirmIn,
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> MessageOut:
    try:
        auth.update_user_password(body.recovery_token, body.new_password)
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc
    if body.email:
        user = db.scalar(select(User).where(User.email == body.email))
        if user is not None:
            user.must_change_password = False
            user.temporary_password_expires_at = None
            user.password_changed_at = datetime.now(timezone.utc)
            db.commit()
    return MessageOut(message="Contrasena restablecida correctamente")
