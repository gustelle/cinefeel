from __future__ import annotations

from pydantic import BaseModel, Field


class Identifiable(BaseModel):
    """
    An object that can be identified by a unique identifier (UID).
    """

    uid: str | None = Field(
        None,
        description="A unique identifier for the object.",
        examples=["12345", "abcde"],
        frozen=True,  # make the field immutable after creation
    )
