from typing import Self

from pydantic import Field, HttpUrl

from src.entities.composable import Composable
from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase, Storable

from .woa import WOAInfluence, WOASpecifications, WOAType, WorkOfArt


class FilmActor(Storable):
    """
    Représente un acteur et ses rôles dans un film.
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


class FilmSummary(Storable):
    """
    le résumé d'un film.
    """

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


class FilmMedia(Storable):
    """
    représente les médias associés à un film, tels que l'affiche, les autres médias et la bande-annonce.
    """

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
        repr=False,
        serialization_alias="realisateurs",
        validation_alias="realisateurs",
    )
    produced_by: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="producteurs",
        validation_alias="producteurs",
    )
    genres: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="genres",
        validation_alias="genres",
    )
    special_effects_by: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="effets_speciaux",
        validation_alias="effets_speciaux",
    )
    scenary_by: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="decorateurs",
        validation_alias="decorateurs",
    )
    written_by: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="scenaristes",
        validation_alias="scenaristes",
    )
    music_by: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="compositeurs_musique",
        validation_alias="compositeurs_musique",
    )
    duration: str | None = Field(
        None,
        description="Durée du film au format HH:MM:SS.",
        examples=["01:30:00", "02:15:45"],
        repr=False,
        serialization_alias="duree_film",
        validation_alias="duree_film",
    )


class Film(Composable, WorkOfArt):
    """ """

    summary: FilmSummary | None = Field(
        None,
        repr=False,
        serialization_alias="resume",
        validation_alias="resume",
    )
    media: FilmMedia | None = Field(
        None,
        repr=False,
        serialization_alias="medias",
        validation_alias="medias",
    )
    influences: list[WOAInfluence] | None = Field(
        None,
        repr=False,
        serialization_alias="influences",
        validation_alias="influences",
    )
    specifications: FilmSpecifications | None = Field(
        None,
        repr=False,
        serialization_alias="fiche_technique",
        validation_alias="fiche_technique",
    )
    actors: list[FilmActor] | None = Field(
        None,
        repr=False,
        serialization_alias="acteurs",
        validation_alias="acteurs",
    )

    @classmethod
    def from_parts(
        cls,
        base_info: SourcedContentBase,
        parts: list[ExtractionResult],
    ) -> Self:
        """
        Compose this entity with other entities or data.

        Args:
            base_info (SourcedContentBase): Base information including title, permalink, and uid.
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.

        Returns:
            Film: A new instance of the composed Film entity.
        """

        additional_fields = {
            "uid": base_info.uid,
            "title": base_info.title,
            "permalink": base_info.permalink,
            "woa_type": WOAType.FILM,
        }

        super_model = cls.construct(parts, **additional_fields)

        # add specific fields for Film
        for part in parts:
            if isinstance(part, WOAInfluence):
                if super_model.influences is None:
                    super_model.influences = []
                super_model.influences.append(part)

        return super_model
