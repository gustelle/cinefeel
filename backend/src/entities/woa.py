from enum import StrEnum

from pydantic import BaseModel, Field

from .person import Person
from .source import Sourcable


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
    Represents the specifications of a work of art.
    """

    title: str = Field(
        ...,
        description="The title of the work of art.",
    )
    other_titles: list[str] | None = Field(
        None,
        repr=False,
    )
    release_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
    )


class WorkOfArt(Sourcable):
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
    Represents the influence of a work of art on another work of art.
    """

    persons: list[Person] | None = Field(
        None,
        description="The persons that influenced the current work of art.",
        repr=False,
    )

    work_of_arts: list[str] | None = Field(
        None,
        description="The works of art that influenced the current work of art.",
        repr=False,
    )
