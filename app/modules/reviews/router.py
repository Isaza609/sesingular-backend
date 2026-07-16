from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Dispute, Order, Product, Review, ReviewReport
from app.models.order import OrderStatus
from app.models.review import DisputeStatus, ReportStatus, ReviewStatus
from app.models.user import User
from app.modules.auth.deps import require_admin
from app.modules.common.permissions import get_seller_store, require_buyer
from app.modules.reviews.schemas import DisputeIn, DisputePatch, ReportIn, ReviewIn

router = APIRouter(tags=["reviews"])


@router.get("/catalog/products/{product_id}/reviews")
def product_reviews(product_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(select(Review).where(Review.product_id == product_id, Review.status == ReviewStatus.published).order_by(Review.created_at.desc())).all()
    return [{"id": row.id, "product_id": row.product_id, "rating": row.rating, "comment": row.comment, "reviewer_name": row.user.name if row.user else None, "created_at": row.created_at} for row in rows]


@router.post("/catalog/products/{product_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(product_id: str, body: ReviewIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    order = db.get(Order, body.order_id)
    if product is None or order is None or order.buyer_id != user.id or order.status != OrderStatus.delivered or not any(item.variant and item.variant.product_id == product_id for item in order.items):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo puedes reseñar productos de pedidos entregados")
    existing = db.scalar(select(Review).where(Review.product_id == product_id, Review.user_id == user.id, Review.order_id == order.id))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya reseñaste este producto en ese pedido")
    review = Review(product_id=product_id, store_id=product.store_id, user_id=user.id, order_id=order.id, rating=body.rating, comment=body.comment, status=ReviewStatus.published)
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"id": review.id, "product_id": review.product_id, "rating": review.rating, "comment": review.comment, "status": review.status.value, "created_at": review.created_at}


@router.post("/reviews/{review_id}/report", status_code=status.HTTP_201_CREATED)
def report_review(review_id: str, body: ReportIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reseña no encontrada")
    report = ReviewReport(review_id=review.id, reporter_id=user.id, reason=body.reason, status=ReportStatus.open)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "status": report.status.value}


@router.get("/orders/{order_id}/dispute")
def order_dispute(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    dispute = db.scalar(select(Dispute).where(Dispute.order_id == order_id).order_by(Dispute.created_at.desc()))
    return None if dispute is None else {"id": dispute.id, "order_id": dispute.order_id, "reason": dispute.reason, "description": dispute.description, "status": dispute.status.value, "resolution_note": dispute.resolution_note, "created_at": dispute.created_at}


@router.post("/orders/{order_id}/dispute", status_code=status.HTTP_201_CREATED)
def create_dispute(order_id: str, body: DisputeIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    dispute = Dispute(order_id=order.id, opened_by=user.id, reason=body.reason, description=body.description, status=DisputeStatus.open)
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return {"id": dispute.id, "order_id": dispute.order_id, "reason": dispute.reason, "description": dispute.description, "status": dispute.status.value, "created_at": dispute.created_at}

