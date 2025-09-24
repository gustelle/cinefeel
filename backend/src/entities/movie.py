import datetime
from typing import Any

from numpy import ndarray
from pydantic import Field, HttpUrl, field_serializer, field_validator

from src.entities.component import EntityComponent
from src.entities.composable import Composable

from .woa import WOAInfluence, WOASpecifications, WOAType, WorkOfArt


class FilmActor(EntityComponent):
    """
    An actor is a real person, playing one or more roles in a film.
    """

    full_name: str = Field(
        ...,
        description="The full name of the actor.",
        examples=["John Doe", "Jane Smith"],
    )
    roles: list[str] | None = Field(
        None,
        description="The list of roles played by the actor in the film.",
        examples=[
            ["Hero", "Villain"],
            ["Supporting Actor"],
            ["Lead Role", "Cameo"],
        ],
    )


class FilmSummary(EntityComponent):

    content: str | None = Field(
        None,
        description="The summary of the film.",
        examples=["A thrilling adventure through time and space."],
    )
    source: str | None = Field(
        None,
        description="The source URL of the summary.",
        examples=["https://example.com/film-summary"],
    )


class FilmMedia(EntityComponent):

    posters: list[HttpUrl] | None = Field(
        None,
    )
    other_medias: list[HttpUrl] | None = Field(
        None,
    )
    trailers: list[HttpUrl] | None = Field(
        None,
    )


class FilmSpecifications(WOASpecifications):
    """
    la fiche technique d'un film.
    Cette classe contient des informations sur les personnes impliquées dans la création du film,
    les genres, les effets spéciaux, le décor, l'écriture et la musique.
    """

    directed_by: list[str] | None = Field(
        None,
    )
    produced_by: list[str] | None = Field(
        None,
    )
    genres: list[str] | None = Field(
        None,
    )
    special_effects_by: list[str] | None = Field(
        None,
    )
    scenary_by: list[str] | None = Field(
        None,
    )
    written_by: list[str] | None = Field(
        None,
    )
    music_by: list[str] | None = Field(
        None,
    )
    duration: str | None = Field(
        None,
        description="Durée du film au format HH:MM:SS.",
        examples=["01:30:00", "02:15:45"],
    )

    @field_validator("duration", mode="before")
    @classmethod
    def load_from_dt(cls, value: Any) -> str | None:
        """case where the duration is provided as a datetime.timedelta object"""
        if isinstance(value, str):
            return value

        if isinstance(value, datetime.time):
            # Convert datetime.time to HH:MM:SS format
            hours = value.hour
            minutes = value.minute
            seconds = value.second
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        return None


class Movie(Composable, WorkOfArt):

    summary: FilmSummary | None = Field(
        None,
    )
    media: FilmMedia | None = Field(
        None,
    )
    influences: list[WOAInfluence] | None = Field(
        None,
    )
    specifications: FilmSpecifications | None = Field(
        None,
    )
    actors: list[FilmActor] | None = Field(
        None,
    )

    woa_type: WOAType = WOAType.MOVIE

    @field_serializer("actors")
    def serialize_dt(self, value: Any):

        # values coming from LLMs or other sources may be numpy arrays
        if isinstance(value, ndarray):
            value = value.tolist()

        return value
