from typing import Self

from pydantic import BaseModel, Field, HttpUrl

from src.entities.composable import Composable
from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase

from .woa import WOAInfluence, WOASpecifications, WOAType, WorkOfArt


class FilmActor(BaseModel):
    """
    Représente un acteur et ses rôles dans un film.
    """

    full_name: str = Field(
        ...,
        description="The full name of the actor.",
        examples=["John Doe", "Jane Smith"],
        repr=False,
        # alias="nom_complet",
        serialization_alias="nom_complet",
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


class FilmSummary(BaseModel):
    """
    le résumé d'un film.
    """

    content: str | None = Field(
        None,
        description="The summary of the film.",
        examples=["A thrilling adventure through time and space."],
        repr=False,
        # alias="contenu_resume",
        serialization_alias="contenu_resume",
    )
    source: str | None = Field(
        None,
        description="The source URL of the summary.",
        examples=["https://example.com/film-summary"],
        repr=False,
        # alias="source_resume",
        serialization_alias="source_resume",
    )


class FilmMedia(BaseModel):
    """
    représente les médias associés à un film, tels que l'affiche, les autres médias et la bande-annonce.
    """

    poster: str | None = Field(
        None,
        repr=False,
        # alias="url_affiche",
        serialization_alias="url_affiche",
    )
    other_media: list[str] | None = Field(
        None,
        repr=False,
        # alias="url_autres_contenus",
        serialization_alias="url_autres_contenus",
    )
    trailer: HttpUrl | None = Field(
        None,
        repr=False,
        # alias="url_bande_annonce",
        serialization_alias="url_bande_annonce",
    )


class FilmSpecifications(WOASpecifications):
    """
    la fiche technique d'un film.
    Cette classe contient des informations sur les personnes impliquées dans la création du film,
    les genres, les effets spéciaux, le décor, l'écriture et la musique.
    """

    directed_by: list[str] | None = Field(
        None,
        repr=False,
        # alias="realisateurs",
        serialization_alias="realisateurs",
    )
    produced_by: list[str] | None = Field(
        None,
        repr=False,
        # alias="producteurs",
        serialization_alias="producteurs",
    )
    genres: list[str] | None = Field(
        None,
        repr=False,
        # alias="genres",
        serialization_alias="genres",
    )
    special_effects_by: list[str] | None = Field(
        None,
        repr=False,
        # alias="effets_speciaux",
        serialization_alias="effets_speciaux",
    )
    scenary_by: list[str] | None = Field(
        None,
        repr=False,
        # alias="decorateurs",
        serialization_alias="decorateurs",
    )
    written_by: list[str] | None = Field(
        None,
        repr=False,
        # alias="scenaristes",
        serialization_alias="scenaristes",
    )
    music_by: list[str] | None = Field(
        None,
        repr=False,
        # alias="compositeurs_musique",
        serialization_alias="compositeurs_musique",
    )
    duration: str | None = Field(
        None,
        description="The duration of the film in HH:MM:SS format.",
        examples=["01:30:00", "02:15:45"],
        repr=False,
        # alias="duree_film",
        serialization_alias="duree_film",
    )


class Film(Composable, WorkOfArt):
    """ """

    summary: FilmSummary | None = Field(
        None,
        repr=False,
        # alias="resume",
        serialization_alias="resume",
    )
    media: FilmMedia | None = Field(
        None,
        repr=False,
        # alias="medias",
        serialization_alias="medias",
    )
    influences: list[WOAInfluence] | None = Field(
        None,
        repr=False,
        # alias="influences",
        serialization_alias="influences",
    )
    specifications: FilmSpecifications | None = Field(
        None,
        repr=False,
        # alias="fiche_technique",
        serialization_alias="fiche_technique",
    )
    actors: list[FilmActor] | None = Field(
        None,
        repr=False,
        # alias="acteurs",
        serialization_alias="acteurs",
    )

    @classmethod
    def from_parts(
        cls,
        base_info: SourcedContentBase,
        parts: list[ExtractionResult],
        by_alias: bool = False,
    ) -> Self:
        """
        Compose this entity with other entities or data.

        Args:
            base_info (SourcedContentBase): Base information including title, permalink, and uid.
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.
            by_alias (bool): Whether to use field aliases for serialization. Defaults to False.

        Returns:
            Film: A new instance of the composed Film entity.
        """

        additional_fields = {
            "uid": base_info.uid,
            "title": base_info.title,
            "permalink": base_info.permalink,
            "woa_type": WOAType.FILM,
        }

        return cls.construct(parts, by_alias=by_alias, **additional_fields)
