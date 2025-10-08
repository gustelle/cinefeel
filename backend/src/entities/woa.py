from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel, Field, field_validator

from src.entities.component import EntityComponent


class WOAType(StrEnum):
    """
    the type of a work of art.
    """

    PAINTING = "painting"
    SCULPTURE = "sculpture"
    DRAWING = "drawing"
    PHOTOGRAPHY = "photography"
    PERFORMANCE = "performance"
    MOVIE = "movie"
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
    )
    release_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
    )


class WorkOfArt(BaseModel):
    """
    Represents a work of art
    """

    woa_type: WOAType | None = Field(
        None,
        description="The type of the work of art. ",
        examples=[str(woa_type) for woa_type in WOAType],
    )


class WOAInfluence(EntityComponent):
    """
    Représente les influences d'une oeuvre d'art.
    """

    persons: list[str] | None = Field(
        None,
        description="les personnes qui ont influencé l'oeuvre d'art actuelle.",
    )

    work_of_arts: list[str] | None = Field(
        None,
        description="les autres oeuvres d'art qui ont influencé l'oeuvre d'art actuelle.",
    )

    @field_validator("persons", "work_of_arts", mode="before")
    @classmethod
    def filter_empty(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and isinstance(v, Iterable):
            return list(filter(lambda x: x is not None and str(x).strip() != "", v))
        return v
