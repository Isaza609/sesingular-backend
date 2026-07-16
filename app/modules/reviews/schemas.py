from pydantic import BaseModel, Field


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    order_id: str


class ReportIn(BaseModel):
    reason: str = Field(min_length=1, max_length=300)


class DisputeIn(BaseModel):
    reason: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)


class DisputePatch(BaseModel):
    status: str = Field(pattern="^(open|in_review|resolved|rejected)$")
    resolution_note: str | None = None

