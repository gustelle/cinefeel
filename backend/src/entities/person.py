from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, HttpUrl, StringConstraints

from src.entities.color import SkinColor
from src.entities.composable import Composable
from src.entities.extraction import ExtractionResult
from src.entities.religion import Religion
from src.entities.sexual_orientation import SexualOrientation
from src.entities.source import SourcedContentBase, Storable


class GenderEnum(StrEnum):
    """
    Enum for the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    UNKNWON = "unknown"


ParentTrade = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=0,
    ),
]  # may be empty for some sections


PersonInfluence = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=0,
    ),
]  # may be empty for some sections


class ChildHoodConditions(Storable):
    """
    Représente les conditions dans lesquelles une personne a grandi pendant son enfance.
    Cette classe contient des informations sur le statut familial, économique, éducatif et l'environnement social de la personne pendant son enfance.
    """

    family_status: str | None = Field(
        None,
        description="le statut familial de la personne pendant l'enfance.",
        repr=False,
        serialization_alias="statut_familial",
        validation_alias="statut_familial",
    )
    economic_status: str | None = Field(
        None,
        description="le statut économique de la personne pendant l'enfance.",
        repr=False,
        serialization_alias="statut_economique",
        validation_alias="statut_economique",
    )
    education_level: str | None = Field(
        None,
        description="le niveau d'éducation de la personne pendant l'enfance.",
        repr=False,
        serialization_alias="niveau_education",
        validation_alias="niveau_education",
    )
    social_environment: str | None = Field(
        None,
        description="l'environnement social de la personne pendant l'enfance.",
        repr=False,
        serialization_alias="environnement_social",
        validation_alias="environnement_social",
    )


class Biography(Storable):
    """
    Représente la biographie d'une personne.
    Cette classe contient des informations sur le nom complet, les surnoms, le genre, les nationalités, la religion, les dates de naissance et de décès,
    """

    full_name: str = Field(
        ...,
        repr=False,
        serialization_alias="nom_complet",
        validation_alias="nom_complet",
    )
    nicknames: list[str] | None = Field(
        None,
        description="les surnoms de la personne. Cette liste peut être utilisée pour filtrer la liste des personnes.",
        repr=False,
        serialization_alias="surnoms",
        validation_alias="surnoms",
    )
    genre: GenderEnum | None = Field(
        None,
        description="Le genre de la personne: homme, femme, non-binaire ou inconnu.",
        repr=False,
        serialization_alias="genre",
        validation_alias="genre",
    )
    nationalities: list[str] | None = Field(
        None,
        description="les nationalités de la personne",
        examples=["français", "américain", "canadien"],
        repr=False,
        serialization_alias="nationalites",
        validation_alias="nationalites",
    )
    religion: Religion | None = Field(
        None,
        repr=False,
        examples=[
            "catholique",
            "musulman",
            "juif",
            "bouddhiste",
            "hindouiste",
            "athée",
        ],
        description="La religion de la personne, par exemple 'catholique', 'musulman', 'juif', 'bouddhiste', 'hindouiste', 'athée'.",
    )
    birth_date: str | None = Field(
        None,
        examples=["01/01/2020"],
        repr=False,
        serialization_alias="date_naissance",
        validation_alias="date_naissance",
        description="La date de naissance de la personne au format ISO 8601 (YYYY-MM-DD).",
    )
    death_date: str | None = Field(
        None,
        examples=["2023-10-01"],
        repr=False,
        serialization_alias="date_deces",
        validation_alias="date_deces",
        description="La date de décès de la personne au format ISO 8601 (YYYY-MM-DD).",
    )
    parents_trades: list[ParentTrade] | None = Field(
        None,
        examples=["charpentier", "banquier"],
        repr=False,
        serialization_alias="metiers_parents",
        validation_alias="metiers_parents",
    )
    education: list[str] | None = Field(
        None,
        examples=["Harvard University", "MIT"],
        repr=False,
        serialization_alias="formation",
        validation_alias="formation",
        description="Liste des formations de la personne, par exemple 'Harvard University', 'MIT'.",
    )
    childhood_conditions: ChildHoodConditions | None = Field(
        None,
        repr=False,
        serialization_alias="conditions_enfance",
        validation_alias="conditions_enfance",
    )


class PersonMedia(Storable):
    """
    représente les contenus multimédias associés à une personne.
    """

    photos: list[HttpUrl] | None = Field(
        None,
        repr=False,
        serialization_alias="photos",
        validation_alias="photos",
    )
    other_medias: list[HttpUrl] | None = Field(
        None,
        repr=False,
        serialization_alias="autres_contenus",
        validation_alias="autres_contenus",
    )


class PersonVisibleFeatures(Storable):
    """
    les caractéristiques visibles d'une personne, telles que la taille, le poids, la couleur de peau, l'obésité, la naine, le handicap et le genre.
    """

    skin_color: SkinColor | None = Field(
        None,
        description="La couleur de peau de la personne, par exemple 'claire', 'mate', 'foncée'.",
        repr=False,
        serialization_alias="couleur_peau",
        validation_alias="couleur_peau",
        examples=["claire", "mate", "foncée"],
    )
    is_obese: bool | None = Field(
        None,
        description="Indique si la personne est obèse.",
        repr=False,
        serialization_alias="est_obese",
        validation_alias="est_obese",
        examples=[True, False],
    )
    is_dwarf: bool | None = Field(
        None,
        description="Indique si la personne est naine.",
        repr=False,
        serialization_alias="est_naine",
        validation_alias="est_naine",
        examples=[True, False],
    )
    is_disabled: bool | None = Field(
        None,
        description="Indique si la personne est handicapée.",
        repr=False,
        serialization_alias="est_handicapee",
        validation_alias="est_handicapee",
        examples=[True, False],
    )
    genre: GenderEnum | None = Field(
        None,
        description="Le genre de la personne: homme, femme, non-binaire ou inconnu.",
        repr=False,
        serialization_alias="genre",
        validation_alias="genre",
    )


class PersonCharacteristics(PersonVisibleFeatures):
    """
    Represente les caractéristiques d'une personne.
    """

    sexual_orientation: SexualOrientation | None = Field(
        None,
        repr=False,
        serialization_alias="orientation_sexuelle",
        validation_alias="orientation_sexuelle",
        examples=["hétérosexuel", "homosexuel", "bisexuel", "autre"],
        description="L'orientation sexuelle de la personne, par exemple 'hétérosexuel', 'homosexuel', 'bisexuel', 'autre'.",
    )


class Person(Composable, SourcedContentBase):
    """
    Represents a person with a name and an optional list of roles.

    """

    biography: Biography | None = Field(
        None,
        repr=False,
    )

    media: PersonMedia | None = Field(
        None,
        repr=False,
    )

    characteristics: PersonCharacteristics | None = Field(
        None,
        repr=False,
    )

    influences: list[PersonInfluence] | None = Field(
        None,
        description="List of influences on the person, such as mentors or significant figures in their life.",
        repr=False,
        serialization_alias="influences",
        validation_alias="influences",
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
            Person: A new instance of the composed Person entity.
        """

        additional_fields = {
            "uid": base_info.uid,
            "title": base_info.title,
            "permalink": base_info.permalink,
        }

        return cls.construct(parts, **additional_fields)
