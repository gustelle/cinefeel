import re

from pydantic import BaseModel, Field, HttpUrl, field_validator
from unidecode import unidecode


class Storable(BaseModel):
    """
    An object that can be stored in a database or a file.
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
        # replace accents and casefold to lowercase
        value = unidecode(value).casefold()

        # constraint of meili:
        # only (a-z A-Z 0-9), hyphens (-) and underscores (_) are allowed
        value = re.sub(r"[^a-z0-9_-]", "", value, flags=re.IGNORECASE)

        # remove quotes
        value = value.replace('"', "").replace("'", "")
        return value


class SourcedContentBase(Storable):
    """
    Base class for contents
    """

    title: str = Field(
        ...,
        description="The title of the information entity.",
        examples=["Stanley Kubrick", "The Shining"],
    )

    permalink: HttpUrl = Field(
        ...,
        description="The permalink to the object, typically a URL.",
        examples=[
            "https://fr.wikipedia.org/wiki/Stanley_Kubrick",
        ],
    )
