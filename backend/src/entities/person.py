from enum import StrEnum

from pydantic import BaseModel, Field

from src.entities.source import SourcedContentBase


class GenderEnum(StrEnum):
    """
    Enum for the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    UNKNWON = "unknown"


class ChildHoodConditions(BaseModel):
    """
    Represents the childhood conditions of a person.
    """

    family_status: str | None = Field(
        None,
        description="The family status of the person during childhood.",
        repr=False,
    )
    economic_status: str | None = Field(
        None,
        description="The economic status of the person during childhood.",
        repr=False,
    )
    education_level: str | None = Field(
        None,
        description="The education level of the person during childhood.",
        repr=False,
    )
    social_environment: str | None = Field(
        None,
        description="The social environment of the person during childhood.",
        repr=False,
    )


class Biography(BaseModel):
    """
    Represents the biography of a person.
    """

    full_name: str = Field(
        ...,
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
    religion: str | None = Field(
        None,
        repr=False,
    )
    birth_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
    )
    death_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
    )
    parents_trades: list[str] | None = Field(
        None,
        examples=["carpenter", "banker", "teacher"],
        repr=False,
    )
    education: list[str] | None = Field(
        None,
        examples=["Harvard University", "MIT"],
        repr=False,
    )
    childhood_conditions: ChildHoodConditions | None = Field(
        None,
        repr=False,
    )


class PersonMedia(BaseModel):
    """ """

    poster: str | None = Field(
        None,
        repr=False,
    )
    other_media: list[str] | None = Field(
        None,
        repr=False,
    )


class PersonCharacteristics(BaseModel):
    """
    Represents the characteristics of a person.
    """

    height: str | None = Field(
        None,
        description="The height of the person.",
        repr=False,
    )
    weight: str | None = Field(
        None,
        description="The weight of the person.",
        repr=False,
    )
    skin_color: str | None = Field(
        None,
        repr=False,
    )
    sexual_orientation: str | None = Field(
        None,
        description="The sexual orientation of the person.",
        repr=False,
    )
    disabilities: list[str] | None = Field(
        None,
        repr=False,
    )


class Person(SourcedContentBase):
    """
    Represents a person with a name and an optional list of roles.

    """

    biography: Biography = Field(
        None,
        repr=False,
    )

    nicknames: list[str] | None = Field(
        None,
        description="The nicknames of the person. This can be used to filter the list of people.",
        repr=False,
    )

    media: PersonMedia | None = Field(
        None,
        repr=False,
    )

    characteristics: PersonCharacteristics | None = Field(
        None,
        repr=False,
    )
