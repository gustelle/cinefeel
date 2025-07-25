from enum import StrEnum

from pydantic import BaseModel, Field

from src.entities.component import EntityComponent

from .person import Person


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


class WOASpecifications(EntityComponent):
    """
    spécifications d'une œuvre d'art.
    """

    title: str = Field(
        ...,
        description="Le titre de l'œuvre d'art.",
    )
    other_titles: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="autres_titres",
        validation_alias="autres_titres",
    )
    release_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
        serialization_alias="date_sortie",
        validation_alias="date_sortie",
    )


class WorkOfArt(BaseModel):
    """
    Represents a work of art
    """

    woa_type: WOAType | None = Field(
        None,
        description="The type of the work of art. ",
        examples=[str(woa_type) for woa_type in WOAType],
        repr=False,
    )


class WOAInfluence(EntityComponent):
    """
    Représente les influences d'une oeuvre d'art.
    """

    persons: list[Person] | None = Field(
        None,
        description="les personnes qui ont influencé l'oeuvre d'art actuelle.",
        repr=False,
        serialization_alias="personnes_influentes",
        validation_alias="personnes_influentes",
    )

    work_of_arts: list[str] | None = Field(
        None,
        description="les autres oeuvres d'art qui ont influencé l'oeuvre d'art actuelle.",
        repr=False,
        serialization_alias="oeuvres_influentes",
        validation_alias="oeuvres_influentes",
    )
