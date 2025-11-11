from pydantic import BaseModel, Field
from typing import Optional


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    id: int
    name: str
    is_auto_generated: bool | None = False

    class Config:
        from_attributes = True
