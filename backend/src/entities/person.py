import re
from enum import StrEnum
from typing import Self

from pydantic import Field, HttpUrl, model_validator

from src.entities.storable import Storable


class GenderEnum(StrEnum):
    """
    Enum for the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    UNKNWON = "unknown"


class Person(Storable):
    """
    Represents a person with a name and an optional list of roles.
    """

    full_name: str
    person_id: str = Field(
        ...,
        description="The ID of the person page on Wikipedia. This is the part of the URL after 'wiki/'",
    )
    other_names: list[str] | None = Field(
        None,
        description="Other names of the person if any.",
    )
    nicknames: list[str] | None = Field(
        None,
        description="The nicknames of the person. This can be used to filter the list of people.",
    )
    genre: GenderEnum | None = Field(
        None,
        description="The genre of the person. This can be used to filter the list of people.",
    )
    nationalities: list[str] | None = Field(
        None,
        description="The nationalities of the person. This can be used to filter the list of people.",
    )

    media: list[HttpUrl] | None = Field(
        None,
        description="The image of the person. This can be used to filter the list of people.",
    )

    @model_validator(mode="after")
    def customize_uid(self) -> Self:
        """override the uid with a custom uid based on the work of art id and type"""

        value = self.person_id.strip()

        value = re.sub(r"[^a-zA-Z0-9]", "_", value)

        # replace spaces with underscores
        value = value.replace(" ", "_")

        # lowercase the uid
        value = value.casefold()

        self.uid = value

        return self
