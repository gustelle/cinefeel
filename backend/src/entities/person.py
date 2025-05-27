from enum import StrEnum

from pydantic import Field

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

    TODO:
    - problem with media
    """

    full_name: str = Field(
        ...,
        repr=False,
    )
    other_names: list[str] | None = Field(
        None, description="Other names of the person if any.", repr=False
    )
    nicknames: list[str] | None = Field(
        None,
        description="The nicknames of the person. This can be used to filter the list of people.",
        repr=False,
    )
    genre: GenderEnum | None = Field(
        None,
        description="The genre of the person. This can be used to filter the list of people.",
        repr=False,
    )
    nationalities: list[str] | None = Field(
        None,
        description="The nationalities of the person. This can be used to filter the list of people.",
        repr=False,
    )

    # media: list[HttpUrl] | None = Field(
    #     None,
    #     description="The image of the person. This can be used to filter the list of people.",
    # )
