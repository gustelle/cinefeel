from enum import StrEnum
from typing import Self

from pydantic import Field

from src.entities.composable import Composable
from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase, Storable


class GenderEnum(StrEnum):
    """
    Enum for the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    UNKNWON = "unknown"


class ChildHoodConditions(Storable):
    """
    Représente les conditions de l'enfance d'une personne.
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
    religion: str | None = Field(
        None,
        repr=False,
    )
    birth_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
        serialization_alias="date_naissance",
        validation_alias="date_naissance",
    )
    death_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
        serialization_alias="date_deces",
        validation_alias="date_deces",
    )
    parents_trades: list[str] | None = Field(
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
        serialization_alias="formations",
        validation_alias="formations",
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

    poster: str | None = Field(
        None,
        repr=False,
        serialization_alias="url_affiche",
        validation_alias="url_affiche",
    )
    other_media: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="url_autres_contenus",
        validation_alias="url_autres_contenus",
    )


class PersonCharacteristics(Storable):
    """
    Represente les caractéristiques d'une personne.
    """

    height: str | None = Field(
        None,
        repr=False,
        serialization_alias="taille",
        validation_alias="taille",
    )
    weight: str | None = Field(
        None,
        repr=False,
        serialization_alias="poids",
        validation_alias="poids",
        examples=["70 kg", "80 kg"],
        description="Le poids de la personne, par exemple '70 kg' ou '80 kg'.",
    )
    skin_color: str | None = Field(
        None,
        repr=False,
        serialization_alias="couleur_peau",
        validation_alias="couleur_peau",
    )
    sexual_orientation: str | None = Field(
        None,
        repr=False,
        serialization_alias="orientation_sexuelle",
        validation_alias="orientation_sexuelle",
    )
    disabilities: list[str] | None = Field(
        None,
        repr=False,
        serialization_alias="handicaps",
        validation_alias="handicaps",
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
