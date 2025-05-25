from pydantic import BaseModel, Field


class Storable(BaseModel):
    """
    Represents a work of art
    """

    uid: str = Field(
        ...,
        description="""
            The unique ID of the object. It must contain no special characters.
            When not provided, a random UUID is generated.
        """,
        examples=["The_Scream", "Starry_Night"],
    )
