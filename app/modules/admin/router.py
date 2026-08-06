from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Dispute, Order, Payment, PaymentEvent, Review, ReviewReport, Store, StoreMember, User
from app.models.payment import PaymentStatus
from app.models.user import UserRole
from app.modules.admin import service
from app.modules.admin.schemas import (
    CommissionIn,
    DisputeOut,
    DisputePatch,
    GatewayIn,
    InventoryReportOut,
    ReportPatch,
    ReportedReviewOut,
    ReviewPatch,
    SalesReportOut,
    SettingOut,
    StoreDetailOut,
    StoreListOut,
    StoreCreate,
    StoreMemberCreate,
    StoreMemberCreateOut,
    StoreMemberOut,
    StoreMemberPatch,
    StoreOut,
    StorePatch,
    TemporaryPasswordOut,
    TransactionEventOut,
    TransactionListOut,
    TransactionOut,
    UserListOut,
    UserCreate,
    UserCreateOut,
    UserOut,
    UserPatch,
)
from app.modules.auth.deps import require_admin
from app.modules.auth.service import AuthServiceError, SupabaseAuthService, get_auth_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

COMMON_RESPONSES = {
    400: {"description": "Datos invalidos o regla de negocio violada."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol admin."},
    404: {"description": "Recurso no encontrado."},
    409: {"description": "Conflicto con recurso existente."},
    422: {"description": "Validacion Pydantic."},
    502: {"description": "Supabase Auth no disponible o no configurado."},
}


def _user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        email=u.email,
        name=u.name,
        phone=u.phone,
        role=u.role.value,
        active=u.active,
        must_change_password=u.must_change_password,
        temporary_password_expires_at=u.temporary_password_expires_at,
        created_at=u.created_at,
    )


def _store_out(s: Store) -> dict:
    return dict(
        id=s.id,
        slug=s.slug,
        name=s.name,
        description=s.description,
        logo_url=s.logo_url,
        contact_email=s.contact_email,
        contact_phone=s.contact_phone,
        active=s.active,
        created_at=s.created_at,
    )


# ---------- usuarios ----------

def _temporary_password() -> str:
    return f"Singular-{secrets.token_urlsafe(9)}"


def _member_out(member: StoreMember) -> StoreMemberOut:
    user = member.user
    return StoreMemberOut(
        user_id=user.id,
        store_id=member.store_id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        platform_role=user.role.value,
        member_role=member.role,
        active=user.active,
        must_change_password=user.must_change_password,
        created_at=member.created_at,
    )


def _auth_id(data: dict, fallback: str | None = None) -> str:
    user = data.get("user") or data
    return str(user.get("id") or user.get("sub") or fallback or "")


def _create_auth_user_or_fail(auth: SupabaseAuthService, email: str, password: str, metadata: dict) -> str:
    try:
        data = auth.admin_create_user(email, password, metadata)
    except AuthServiceError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    user_id = _auth_id(data)
    if not user_id:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Supabase Auth no retorno identificador de usuario")
    return user_id


@router.get(
    "/users",
    response_model=UserListOut,
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios",
    description="Rol permitido: admin. HU-USR-05. Lista usuarios de plataforma con filtros de rol y estado.",
    response_description="Lista paginada de usuarios.",
    responses=COMMON_RESPONSES,
)
def list_users(
    q: str | None = None,
    role: str | None = Query(None, pattern="^(buyer|seller|admin)$"),
    active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, total = service.list_users(db, q, role, active, page, page_size)
    return UserListOut(total=total, page=page, page_size=page_size, items=[_user_out(u) for u in rows])


@router.post(
    "/users",
    response_model=UserCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description=(
        "Rol permitido: admin. HU-USR-02 y HU-USR-05. Crea usuarios no autorregistrables "
        "con credencial temporal cuando el rol es seller o admin."
    ),
    response_description="Usuario creado; si aplica, incluye credencial temporal visible una sola vez.",
    responses=COMMON_RESPONSES,
)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
):
    if (body.id and db.get(User, body.id) is not None) or db.scalar(select(User).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El usuario ya existe")
    temporary_password = None
    expires_at = None
    user_id = body.id
    must_change = body.role in ("seller", "admin")
    if must_change:
        temporary_password = body.temporary_password or _temporary_password()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=body.temporary_password_hours)
        user_id = _create_auth_user_or_fail(
            auth,
            body.email,
            temporary_password,
            {"name": body.name, "full_name": body.name, "role": body.role},
        )
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "id es requerido para crear compradores desde administracion")
    user = User(
        id=user_id,
        email=body.email,
        name=body.name,
        phone=body.phone,
        role=UserRole(body.role),
        must_change_password=must_change,
        temporary_password_expires_at=expires_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserCreateOut(**_user_out(user).model_dump(), temporary_password=temporary_password)


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar usuario",
    description="Rol permitido: admin. HU-USR-05. Consulta un usuario de plataforma por identificador.",
    response_description="Usuario encontrado.",
    responses=COMMON_RESPONSES,
)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return _user_out(user)


@router.patch(
    "/users/{user_id}",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar usuario",
    description="Rol permitido: admin. HU-USR-05. Actualiza rol o estado activo de un usuario sin borrar historico.",
    response_description="Usuario actualizado.",
    responses=COMMON_RESPONSES,
)
def patch_user(
    user_id: str,
    body: UserPatch,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if user.id == admin.id and body.active is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes desactivar tu propia cuenta")
    if user.id == admin.id and body.role and body.role != "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes cambiar tu propio rol")
    if body.active is not None:
        user.active = body.active
    if body.role:
        user.role = UserRole(body.role)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post(
    "/users/{user_id}/temporary-password",
    response_model=TemporaryPasswordOut,
    status_code=status.HTTP_200_OK,
    summary="Regenerar credencial temporal",
    description=(
        "Rol permitido: admin. HU-USR-02. Invalida la contrasena anterior en Supabase, "
        "genera una nueva credencial temporal y fuerza cambio en el siguiente ingreso."
    ),
    response_description="Usuario actualizado con nueva credencial temporal visible una sola vez.",
    responses=COMMON_RESPONSES,
)
def regenerate_temporary_password(
    user_id: str,
    hours: int = Query(24, ge=1, le=168, description="Horas de vigencia de la nueva credencial temporal."),
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    temporary_password = _temporary_password()
    try:
        auth.admin_update_user_password(user.id, temporary_password)
    except AuthServiceError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    user.must_change_password = True
    user.temporary_password_expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    db.commit()
    db.refresh(user)
    return TemporaryPasswordOut(user=_user_out(user), temporary_password=temporary_password)


# ---------- tiendas ----------

@router.get("/stores", response_model=StoreListOut)
def list_stores(
    q: str | None = None,
    active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, total = service.list_stores(db, q, active, page, page_size)
    return StoreListOut(
        total=total, page=page, page_size=page_size, items=[StoreOut(**_store_out(s)) for s in rows]
    )


@router.post("/stores", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def create_store(body: StoreCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Store).where(Store.slug == body.slug)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El slug de tienda ya existe")
    if body.owner_user_id:
        owner = db.get(User, body.owner_user_id)
        if owner is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vendedor no encontrado")
        owner.role = UserRole.seller
    store = Store(**body.model_dump(exclude={"owner_user_id"}))
    db.add(store)
    db.flush()
    if body.owner_user_id:
        db.add(StoreMember(store_id=store.id, user_id=body.owner_user_id, role="owner"))
    db.commit()
    db.refresh(store)
    return StoreOut(**_store_out(store))


@router.get("/stores/{store_id}", response_model=StoreDetailOut)
def get_store(store_id: str, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tienda no encontrada")
    return StoreDetailOut(**_store_out(store), **service.store_counts(db, store_id))


@router.patch("/stores/{store_id}", response_model=StoreOut)
def patch_store(store_id: str, body: StorePatch, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tienda no encontrada")
    store.active = body.active
    db.commit()
    db.refresh(store)
    return StoreOut(**_store_out(store))


@router.get(
    "/stores/{store_id}/members",
    response_model=list[StoreMemberOut],
    status_code=status.HTTP_200_OK,
    summary="Listar miembros de tienda",
    description="Rol permitido: admin. HU-USR-05. Lista usuarios activos e inactivos asociados a una tienda.",
    response_description="Miembros de la tienda.",
    responses=COMMON_RESPONSES,
)
def list_store_members(store_id: str, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tienda no encontrada")
    members = db.scalars(
        select(StoreMember).where(StoreMember.store_id == store_id).order_by(StoreMember.created_at)
    ).all()
    return [_member_out(member) for member in members]


@router.post(
    "/stores/{store_id}/members",
    response_model=StoreMemberCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear miembro de tienda",
    description=(
        "Rol permitido: admin. HU-USR-05. Crea un usuario adicional asociado a una tienda, "
        "con credencial temporal y acceso al mismo panel de la tienda."
    ),
    response_description="Miembro creado con credencial temporal visible una sola vez.",
    responses=COMMON_RESPONSES,
)
def create_store_member(
    store_id: str,
    body: StoreMemberCreate,
    db: Session = Depends(get_db),
    auth: SupabaseAuthService = Depends(get_auth_service),
):
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tienda no encontrada")
    if db.scalar(select(User).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El usuario ya existe")
    temporary_password = body.temporary_password or _temporary_password()
    user_id = _create_auth_user_or_fail(
        auth,
        body.email,
        temporary_password,
        {"name": body.name, "full_name": body.name, "role": "seller", "store_id": store_id},
    )
    user = User(
        id=user_id,
        email=body.email,
        name=body.name,
        phone=body.phone,
        role=UserRole.seller,
        must_change_password=True,
        temporary_password_expires_at=datetime.now(timezone.utc) + timedelta(hours=body.temporary_password_hours),
    )
    member = StoreMember(store_id=store_id, user_id=user.id, role=body.member_role)
    db.add(user)
    db.add(member)
    db.commit()
    db.refresh(member)
    return StoreMemberCreateOut(**_member_out(member).model_dump(), temporary_password=temporary_password)


@router.patch(
    "/stores/{store_id}/members/{user_id}",
    response_model=StoreMemberOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar miembro de tienda",
    description="Rol permitido: admin. HU-USR-05. Cambia estado o rol interno del usuario de equipo sin borrar historico.",
    response_description="Miembro actualizado.",
    responses=COMMON_RESPONSES,
)
def patch_store_member(store_id: str, user_id: str, body: StoreMemberPatch, db: Session = Depends(get_db)):
    member = db.scalar(select(StoreMember).where(StoreMember.store_id == store_id, StoreMember.user_id == user_id))
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miembro de tienda no encontrado")
    if body.member_role is not None:
        member.role = body.member_role
    if body.active is not None:
        member.user.active = body.active
    db.commit()
    db.refresh(member)
    return _member_out(member)


# ---------- configuración ----------

@router.get("/settings", response_model=list[SettingOut])
def get_settings(db: Session = Depends(get_db)):
    return [
        SettingOut(key=s.key, value=s.value, updated_at=s.updated_at)
        for s in service.get_settings_masked(db)
    ]


@router.put("/settings/commission", response_model=SettingOut)
def put_commission(
    body: CommissionIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    row = service.upsert_setting(db, "commission", body.model_dump(), admin.id)
    return SettingOut(key=row.key, value=row.value, updated_at=row.updated_at)


@router.put("/settings/payment-gateway", response_model=SettingOut)
def put_gateway(body: GatewayIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    row = service.update_gateway(db, body.model_dump(), admin.id)
    masked = dict(row.value)
    for field in service.SECRET_GATEWAY_FIELDS:
        secret = masked.get(field) or ""
        masked[field] = f"****{secret[-4:]}" if secret else ""
    return SettingOut(key=row.key, value=masked, updated_at=row.updated_at)


# ---------- reportes ----------

@router.get("/reports/sales", response_model=SalesReportOut)
def report_sales(
    date_from: date | None = None,
    date_to: date | None = None,
    store_id: str | None = None,
    channel: str | None = Query(None, pattern="^(online|presencial)$"),
    db: Session = Depends(get_db),
):
    return service.sales_report(db, date_from, date_to, store_id, channel)


@router.get("/reports/inventory", response_model=InventoryReportOut)
def report_inventory(store_id: str | None = None, db: Session = Depends(get_db)):
    return service.inventory_report(db, store_id)


# ---------- moderación ----------

@router.get("/moderation/reviews", response_model=list[ReportedReviewOut])
def moderation_reviews(
    status_filter: str | None = Query(None, alias="status", pattern="^(open|resolved|dismissed)$"),
    db: Session = Depends(get_db),
):
    rows = service.reported_reviews(db, status_filter)
    return [
        ReportedReviewOut(
            report_id=report.id,
            report_reason=report.reason,
            report_status=report.status.value,
            report_created_at=report.created_at,
            review_id=review.id,
            review_status=review.status.value,
            rating=review.rating,
            comment=review.comment,
            product_name=product_name,
            store_name=store_name,
            reviewer_name=reviewer_name,
        )
        for report, review, product_name, store_name, reviewer_name in rows
    ]


@router.patch("/moderation/reviews/{review_id}")
def patch_review(review_id: str, body: ReviewPatch, db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reseña no encontrada")
    review.status = body.status
    db.commit()
    return {"id": review.id, "status": body.status}


@router.patch("/moderation/reports/{report_id}")
def patch_report(report_id: str, body: ReportPatch, db: Session = Depends(get_db)):
    report = db.get(ReviewReport, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado")
    report.status = body.status
    report.resolution_note = body.resolution_note or None
    report.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": report.id, "status": body.status}


@router.get("/moderation/disputes", response_model=list[DisputeOut])
def moderation_disputes(
    status_filter: str | None = Query(
        None, alias="status", pattern="^(open|in_review|resolved|rejected)$"
    ),
    db: Session = Depends(get_db),
):
    rows = service.list_disputes(db, status_filter)
    return [
        DisputeOut(
            id=dispute.id,
            order_id=dispute.order_id,
            reason=dispute.reason,
            description=dispute.description,
            status=dispute.status.value,
            resolution_note=dispute.resolution_note,
            store_name=store_name,
            opener_name=opener_name,
            created_at=dispute.created_at,
        )
        for dispute, store_name, opener_name in rows
    ]


@router.patch("/moderation/disputes/{dispute_id}")
def patch_dispute(dispute_id: str, body: DisputePatch, db: Session = Depends(get_db)):
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disputa no encontrada")
    dispute.status = body.status
    dispute.resolution_note = body.resolution_note or None
    if body.status in ("resolved", "rejected"):
        dispute.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": dispute.id, "status": body.status}


# --- Conciliacion de transacciones (HU-PAG-09) ------------------------------


def _transaction_out(payment: Payment, *, with_events: bool = False) -> dict:
    order = payment.order
    store = order.store if order else None
    buyer = order.buyer if order else None
    data = {
        "id": payment.id,
        "order_id": payment.order_id,
        "store_id": order.store_id if order else None,
        "store_name": store.name if store else None,
        "buyer_id": order.buyer_id if order else None,
        "buyer_name": buyer.name if buyer else None,
        "provider": payment.provider,
        "method": payment.method,
        "status": payment.status.value,
        "amount": payment.amount,
        "received_amount": payment.received_amount,
        "currency": payment.currency,
        "created_at": payment.created_at,
        "events": [],
    }
    if with_events:
        data["events"] = [
            {
                "id": event.id,
                "from_status": event.from_status,
                "to_status": event.to_status,
                "actor_role": event.actor_role,
                "actor_user_id": event.actor_user_id,
                "received_amount": event.received_amount,
                "note": event.note,
                "created_at": event.created_at,
            }
            for event in sorted(payment.events, key=lambda e: e.created_at)
        ]
    return data


@router.get(
    "/transactions",
    response_model=TransactionListOut,
    status_code=status.HTTP_200_OK,
    summary="Listar transacciones para conciliacion",
    description=(
        "Rol permitido: admin. HU-PAG-09. Lista las transacciones (pasarela y manuales) con su "
        "estado y trazabilidad hacia pedido, tienda y metodo de pago, con filtros para conciliar."
    ),
    response_description="Transacciones que cumplen los filtros.",
    responses=COMMON_RESPONSES,
)
def list_transactions(
    transaction_status: str | None = Query(default=None, alias="status", pattern="^(pending|in_review|incomplete|paid|rejected|refunded)$", description="Filtra por estado de la transaccion."),
    store_id: str | None = Query(default=None, description="Filtra por tienda."),
    method: str | None = Query(default=None, description="Filtra por metodo de pago (card, transfer, breb, cash...)."),
    order_id: str | None = Query(default=None, description="Filtra por pedido."),
    date_from: date | None = Query(default=None, description="Fecha inicial inclusiva (por created_at)."),
    date_to: date | None = Query(default=None, description="Fecha final inclusiva (por created_at)."),
    db: Session = Depends(get_db),
):
    stmt = select(Payment).join(Order, Payment.order_id == Order.id)
    if transaction_status:
        stmt = stmt.where(Payment.status == PaymentStatus(transaction_status))
    if store_id:
        stmt = stmt.where(Order.store_id == store_id)
    if method:
        stmt = stmt.where(Payment.method == method)
    if order_id:
        stmt = stmt.where(Payment.order_id == order_id)
    if date_from:
        stmt = stmt.where(Payment.created_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
    if date_to:
        stmt = stmt.where(Payment.created_at <= datetime.combine(date_to, datetime.max.time(), timezone.utc))
    rows = db.scalars(stmt.order_by(Payment.created_at.desc())).unique().all()
    items = [_transaction_out(row) for row in rows]
    return {"items": items, "total": len(items)}


@router.get(
    "/transactions/{payment_id}",
    response_model=TransactionOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar transaccion con historial",
    description=(
        "Rol permitido: admin. HU-PAG-09. Detalle de una transaccion con su historial completo de "
        "estados (eventos), conservando los estados anteriores para conciliacion y auditoria."
    ),
    response_description="Transaccion con su historial de estados.",
    responses=COMMON_RESPONSES,
)
def get_transaction(payment_id: str, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaccion no encontrada")
    return _transaction_out(payment, with_events=True)
