from enum import StrEnum

from pydantic import BaseModel, Field

from src.entities.source import SourcedContentBase


class GenderEnum(StrEnum):
    """
    Enum for the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    UNKNWON = "unknown"


class ChildHoodConditions(BaseModel):
    """
    Représente les conditions de l'enfance d'une personne.
    Cette classe contient des informations sur le statut familial, économique, éducatif et l'environnement social de la personne pendant son enfance.
    """

    family_status: str | None = Field(
        None,
        description="le statut familial de la personne pendant l'enfance.",
        repr=False,
        alias="statut_familial",
        serialization_alias="statut_familial",
    )
    economic_status: str | None = Field(
        None,
        description="le statut économique de la personne pendant l'enfance.",
        repr=False,
        alias="statut_economique",
        serialization_alias="statut_economique",
    )
    education_level: str | None = Field(
        None,
        description="le niveau d'éducation de la personne pendant l'enfance.",
        repr=False,
        alias="niveau_education",
        serialization_alias="niveau_education",
    )
    social_environment: str | None = Field(
        None,
        description="l'environnement social de la personne pendant l'enfance.",
        repr=False,
        alias="environnement_social",
        serialization_alias="environnement_social",
    )


class Biography(BaseModel):
    """
    Représente la biographie d'une personne.
    Cette classe contient des informations sur le nom complet, les surnoms, le genre, les nationalités, la religion, les dates de naissance et de décès,
    """

    full_name: str = Field(
        ...,
        repr=False,
        alias="nom_complet",
        serialization_alias="nom_complet",
    )
    nicknames: list[str] | None = Field(
        None,
        description="les surnoms de la personne. Cette liste peut être utilisée pour filtrer la liste des personnes.",
        repr=False,
        alias="surnoms",
        serialization_alias="surnoms",
    )
    genre: GenderEnum | None = Field(
        None,
        description="Le genre de la personne: homme, femme, non-binaire ou inconnu.",
        repr=False,
        alias="genre",
        serialization_alias="genre",
    )
    nationalities: list[str] | None = Field(
        None,
        description="The nationalities of the person. This can be used to filter the list of people.",
        repr=False,
    )
    religion: str | None = Field(
        None,
        repr=False,
    )
    birth_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
        alias="date_naissance",
        serialization_alias="date_naissance",
    )
    death_date: str | None = Field(
        None,
        examples=["2023-10-01", "2023-10-02"],
        repr=False,
        alias="date_deces",
        serialization_alias="date_deces",
    )
    parents_trades: list[str] | None = Field(
        None,
        examples=["charpentier", "banquier"],
        repr=False,
        alias="metiers_parents",
        serialization_alias="metiers_parents",
    )
    education: list[str] | None = Field(
        None,
        examples=["Harvard University", "MIT"],
        repr=False,
        alias="formations",
        serialization_alias="formations",
    )
    childhood_conditions: ChildHoodConditions | None = Field(
        None,
        repr=False,
        alias="conditions_enfance",
        serialization_alias="conditions_enfance",
    )


class PersonMedia(BaseModel):
    """
    représente les contenus multimédias associés à une personne.
    """

    poster: str | None = Field(
        None,
        repr=False,
        alias="url_affiche",
        serialization_alias="url_affiche",
    )
    other_media: list[str] | None = Field(
        None,
        repr=False,
        alias="url_autres_contenus",
        serialization_alias="url_autres_contenus",
    )


class PersonCharacteristics(BaseModel):
    """
    Represente les caractéristiques d'une personne.
    """

    height: str | None = Field(
        None,
        repr=False,
        alias="taille",
        serialization_alias="taille",
    )
    weight: str | None = Field(
        None,
        repr=False,
        alias="poids",
        serialization_alias="poids",
    )
    skin_color: str | None = Field(
        None,
        repr=False,
        alias="couleur_peau",
        serialization_alias="couleur_peau",
    )
    sexual_orientation: str | None = Field(
        None,
        repr=False,
        alias="orientation_sexuelle",
        serialization_alias="orientation_sexuelle",
    )
    disabilities: list[str] | None = Field(
        None,
        repr=False,
        alias="handicaps",
        serialization_alias="handicaps",
    )


class Person(SourcedContentBase):
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
