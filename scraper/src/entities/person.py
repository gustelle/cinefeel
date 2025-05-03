from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class GenderEnum(StrEnum):
    """
    Enum for the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    OTHER = "other"


class Person(BaseModel):
    """
    Represents a person with a name and an optional list of roles.
    """

    uid: str | None = Field(
        None,
        description="The unique ID of the person. This is used to identify the person in the database.",
    )
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
    roles: list[str] | None = Field(
        None,
        description="The roles of the person. This can be used to filter the list of people.",
    )

    media: list[HttpUrl] | None = Field(
        None,
        description="The image of the person. This can be used to filter the list of people.",
    )
