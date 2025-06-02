from enum import StrEnum

from pydantic import BaseModel, Field

from .person import Person
from .source import SourcedContentBase


class WOAType(StrEnum):
    """
    Enum representing the type of work of art.
    """

    PAINTING = "painting"
    SCULPTURE = "sculpture"
    DRAWING = "drawing"
    PHOTOGRAPHY = "photography"
    PERFORMANCE = "performance"
    FILM = "film"
    SERIES = "series"
    DOCUMENTARY = "documentary"
    ANIMATION = "animation"
    THEATRE = "theatre"
    OPERA = "opera"
    MUSICAL = "musical"
    MUSIC = "music"
    OTHER = "other"


class WOASpecifications(BaseModel):
    """
    Représente les spécifications d'une œuvre d'art.
    Cette classe contient des informations sur le titre, les autres titres et la date de sortie de l'œuvre d'art.
    """

    title: str = Field(
        ...,
        description="Le titre de l'œuvre d'art.",
    )
    other_titles: list[str] | None = Field(
        None,
        repr=False,
        alias="autres_titres",
        serialization_alias="autres_titres",
    )
    release_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
        alias="date_sortie",
        serialization_alias="date_sortie",
    )


class WorkOfArt(SourcedContentBase):
    """
    Represents a work of art
    """

    woa_type: WOAType | None = Field(
        None,
        description="The type of the work of art. ",
        examples=[str(woa_type) for woa_type in WOAType],
        repr=False,
    )


class WOAInfluence(BaseModel):
    """
    Représente les influences d'une œuvre d'art.
    """

    persons: list[Person] | None = Field(
        None,
        description="les personnes qui ont influencé l'œuvre d'art actuelle.",
        repr=False,
        alias="personnes_influentes",
        serialization_alias="personnes_influentes",
    )

    work_of_arts: list[str] | None = Field(
        None,
        description="les œuvres d'art qui ont influencé l'œuvre d'art actuelle.",
        repr=False,
        alias="oeuvres_influentes",
        serialization_alias="oeuvres_influentes",
    )
