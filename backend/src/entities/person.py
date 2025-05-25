from enum import StrEnum

from pydantic import Field, HttpUrl

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
