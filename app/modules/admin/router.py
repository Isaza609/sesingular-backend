from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Dispute, Review, ReviewReport, Store, StoreMember, User
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
    StoreOut,
    StorePatch,
    UserListOut,
    UserCreate,
    UserOut,
    UserPatch,
)
from app.modules.auth.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        email=u.email,
        name=u.name,
        phone=u.phone,
        role=u.role.value,
        active=u.active,
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

@router.get("/users", response_model=UserListOut)
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


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    if db.get(User, body.id) is not None or db.scalar(select(User).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El usuario ya existe")
    user = User(id=body.id, email=body.email, name=body.name, phone=body.phone, role=UserRole(body.role))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return _user_out(user)


@router.patch("/users/{user_id}", response_model=UserOut)
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
