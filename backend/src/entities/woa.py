from enum import StrEnum
from typing import Mapping

from pydantic import Field

from .person import Person
from .storable import Storable


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


class WorkOfArt(Storable):
    """
    Represents a work of art
    """

    title: str
    other_titles: list[str] | None = Field(
        None,
        description="Other titles of the work of art if any.",
    )
    authors: list[Person] | None = Field(
        None,
        description="The authors of the work of art. This can be used to filter the list of works of art.",
    )
    roles: Mapping[str, list[Person]] | None = Field(
        None,
        description="The roles of the persons in the work of art. This can be used to filter the list of works of art.",
        examples=[
            {
                "director": ["Person 1", "Person 2"],
                "actor": ["Person 3", "Person 4"],
            },
        ],
    )

    woa_type: WOAType | None = Field(
        None,
        description="The type of the work of art. ",
        examples=[str(woa_type) for woa_type in WOAType],
    )
