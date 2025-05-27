import re

from pydantic import BaseModel, Field, field_validator


class Storable(BaseModel):
    """
    Represents a work of art

    TODO:
    - testing of the uid field
    """

    uid: str = Field(
        ...,
        description="""
            The unique ID of the object. It must contain no special characters.
            When not provided, a random UUID is generated.
        """,
        examples=["The_Scream", "Starry_Night"],
    )

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, value: str) -> str:
        """
        Validate the uid to ensure it contains no special characters.
        """
        # casefold to lowercase
        value = value.casefold()

        # constraint of meili:
        # only (a-z A-Z 0-9), hyphens (-) and underscores (_) are allowed
        value = re.sub(r"[^a-z0-9_-]", "", value, flags=re.IGNORECASE)

        # remove quotes
        value = value.replace('"', "").replace("'", "")
        return value
