from uuid import uuid4

from pydantic import BaseModel, Field


class Storable(BaseModel):
    """
    Represents a work of art
    """

    uid: str | None = Field(
        default_factory=lambda: str(uuid4()),
        description="""
            The unique ID of the object. It must contain no special characters.
            When not provided, a random UUID is generated.
        """,
        examples=["woa_The_Scream", "woa_Starry_Night"],
        pattern=r"^[a-zA-Z0-9_]+$",
    )
