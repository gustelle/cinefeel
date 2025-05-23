import re
from enum import StrEnum
from typing import Mapping, Self

from pydantic import Field, model_validator

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
    woa_id: str = Field(
        ...,
        description="The ID of the work of art page on Wikipedia. This is the part of the URL after 'wiki/'",
        examples=["The_Scream", "Starry_Night"],
    )

    @model_validator(mode="after")
    def customize_uid(self) -> Self:
        """override the uid with a custom uid based on the work of art id and type"""

        value = self.woa_id.strip()

        if self.woa_type is not None:
            # set the uid to the work of art id
            value = f"{self.woa_type}_{value}"
        else:
            # set the uid to the work of art id
            value = f"woa_{value}"

        value = re.sub(r"[^a-zA-Z0-9]", "_", value)

        # replace spaces with underscores
        value = value.replace(" ", "_")

        # lowercase the uid
        value = value.casefold()

        self.uid = value

        return self
