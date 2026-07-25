from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.modules.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class MeResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None = None
    role: str
    active: bool
    points: int = 0
    tier: str | None = None
    created_at: datetime | None = None


class ProfilePatch(BaseModel):
    name: str | None = None
    phone: str | None = None


def _me(user: User) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role.value,
        active=user.active,
        points=user.points,
        tier=user.tier,
        created_at=user.created_at,
    )


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return _me(user)


@router.patch("/me", response_model=MeResponse)
def patch_me(
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return _me(user)
