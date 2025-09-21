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
        repr=False,
        serialization_alias="nom_complet",
        validation_alias="nom_complet",
    )
    roles: list[str] | None = Field(
        None,
        description="The list of roles played by the actor in the film.",
        examples=[
            ["Hero", "Villain"],
            ["Supporting Actor"],
            ["Lead Role", "Cameo"],
        ],
        repr=False,
    )


class FilmSummary(EntityComponent):

    content: str | None = Field(
        None,
        description="The summary of the film.",
        examples=["A thrilling adventure through time and space."],
        repr=False,
        serialization_alias="contenu_resume",
        validation_alias="contenu_resume",
    )
    source: str | None = Field(
        None,
        description="The source URL of the summary.",
        examples=["https://example.com/film-summary"],
        repr=False,
        serialization_alias="source_resume",
        validation_alias="source_resume",
    )


class FilmMedia(EntityComponent):

    posters: list[HttpUrl] | None = Field(
        None,
        repr=False,
        serialization_alias="affiches",
        validation_alias="affiches",
    )
    other_medias: list[HttpUrl] | None = Field(
        None,
        repr=False,
        serialization_alias="autres_contenus",
        validation_alias="autres_contenus",
    )
    trailers: list[HttpUrl] | None = Field(
        None,
        repr=False,
        serialization_alias="bandes_annonces",
        validation_alias="bandes_annonces",
    )


class FilmSpecifications(WOASpecifications):
    """
    la fiche technique d'un film.
    Cette classe contient des informations sur les personnes impliquées dans la création du film,
    les genres, les effets spéciaux, le décor, l'écriture et la musique.
    """

    directed_by: list[str] | None = Field(
        None,
        serialization_alias="realisateurs",
        validation_alias="realisateurs",
    )
    produced_by: list[str] | None = Field(
        None,
        serialization_alias="producteurs",
        validation_alias="producteurs",
    )
    genres: list[str] | None = Field(
        None,
        serialization_alias="genres",
        validation_alias="genres",
    )
    special_effects_by: list[str] | None = Field(
        None,
        serialization_alias="effets_speciaux",
        validation_alias="effets_speciaux",
    )
    scenary_by: list[str] | None = Field(
        None,
        serialization_alias="decorateurs",
        validation_alias="decorateurs",
    )
    written_by: list[str] | None = Field(
        None,
        serialization_alias="scenaristes",
        validation_alias="scenaristes",
    )
    music_by: list[str] | None = Field(
        None,
        serialization_alias="compositeurs_musique",
        validation_alias="compositeurs_musique",
    )
    duration: str | None = Field(
        None,
        description="Durée du film au format HH:MM:SS.",
        examples=["01:30:00", "02:15:45"],
        serialization_alias="duree_film",
        validation_alias="duree_film",
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
        serialization_alias="resume",
        validation_alias="resume",
    )
    media: FilmMedia | None = Field(
        None,
        serialization_alias="medias",
        validation_alias="medias",
    )
    influences: list[WOAInfluence] | None = Field(
        None,
    )
    specifications: FilmSpecifications | None = Field(
        None,
        serialization_alias="fiche_technique",
        validation_alias="fiche_technique",
    )
    actors: list[FilmActor] | None = Field(
        None,
        serialization_alias="acteurs",
        validation_alias="acteurs",
    )

    woa_type: WOAType = WOAType.MOVIE

    @field_serializer("actors")
    def serialize_dt(self, value: Any):

        # values coming from LLMs or other sources may be numpy arrays
        if isinstance(value, ndarray):
            value = value.tolist()

        return value
