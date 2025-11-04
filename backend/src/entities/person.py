from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Iterable, Self

from pydantic import Field, HttpUrl, StringConstraints, field_validator, model_validator

from src.entities.color import SkinColor
from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.sexual_orientation import SexualOrientation
from src.entities.woa import WOAInfluence


class GenderEnum(StrEnum):
    """
    the genre of a person.
    """

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    UNKNWON = "unknown"


ParentTrade = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
    ),
]  # may be empty for some sections


class ChildHoodConditions(EntityComponent):
    """
    Représente les conditions dans lesquelles une personne a grandi pendant son enfance.
    """

    parents_trades: list[ParentTrade] | None = Field(
        None,
        examples=["charpentier", "banquier"],
    )


class Biography(EntityComponent):

    full_name: str | None = Field(
        None,
        description="Le nom complet de la personne.",
        examples=["Jean Dupont"],
    )

    gender: GenderEnum | None = Field(
        None,
        description="Le genre de la personne: homme, femme, non-binaire ou inconnu.",
    )

    nicknames: list[str] | None = Field(
        None,
        description="Les surnoms de la personne.",
        examples=[["Le Grand", "JD"]],
    )

    nationalities: list[str] | None = Field(
        None,
        description="les nationalités de la personne",
        examples=["français", "américain", "canadien"],
    )

    birth_date: str | None = Field(
        None,
        examples=["2023-10-01"],
        description="La date de naissance de la personne au format ISO 8601 (YYYY-MM-DD).",
    )
    death_date: str | None = Field(
        None,
        examples=["2023-10-01"],
        description="La date de décès de la personne au format ISO 8601 (YYYY-MM-DD).",
    )

    childhood_conditions: ChildHoodConditions | None = Field(
        None,
    )

    @field_validator("nicknames", "nationalities", mode="before")
    @classmethod
    def filter_empty(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and isinstance(v, Iterable):
            return list(filter(lambda x: x is not None and str(x).strip() != "", v))
        return v

    @field_validator("birth_date", "death_date", mode="before")
    @classmethod
    def load_from_dt(cls, value: Any) -> str | None:
        """case when loading from a datetime.date object
        which occurs when loading from duckdb JSON files

        TODO:
        - remove this code since duckdb is not used anymore?
        """

        if isinstance(value, datetime):
            # Convert datetime.time to HH:MM:SS format
            return value.isoformat().split("T")[0]  # Return only the date part

        return str(value) if value else None


class PersonMedia(EntityComponent):
    """
    représente les contenus multimédias associés à une personne.
    """

    photos: list[HttpUrl] | None = Field(
        None,
    )
    other_medias: list[HttpUrl] | None = Field(
        None,
    )


class PersonVisibleFeatures(EntityComponent):
    """
    les caractéristiques visibles d'une personne, telles que la taille, le poids, la couleur de peau, l'obésité, la naine, le handicap et le genre.
    """

    skin_color: SkinColor | None = Field(
        None,
        description="La couleur de peau de la personne, par exemple 'claire', 'mate', 'foncée'.",
    )
    is_obese: bool | None = Field(
        None,
        description="Indique si la personne est obèse.",
        examples=[True, False],
    )
    # is_dwarf: bool | None = Field(
    #     None,
    #     description="Indique si la personne est naine.",
    #     examples=[True, False],
    # )
    # is_disabled: bool | None = Field(
    #     None,
    #     description="Indique si la personne est handicapée.",
    #     examples=[True, False],
    # )


class PersonCharacteristics(PersonVisibleFeatures):
    """
    Represente les caractéristiques d'une personne.
    """

    sexual_orientation: SexualOrientation | None = Field(
        None,
        description="par exemple 'hétérosexuel', 'homosexuel', 'bisexuel', 'autre'.",
    )


class Person(Composable):

    biography: Biography | None = Field(
        None,
    )

    media: PersonMedia | None = Field(
        None,
    )

    # characteristics: PersonCharacteristics | None = Field(
    #     None,
    # )

    influences: list[WOAInfluence] | None = Field(
        None,
    )

    @model_validator(mode="after")
    def set_default_fullname(self) -> Self:
        """
        Set the default full name for the person based on the title.
        """

        if self.biography is not None and self.biography.full_name is None:
            self.biography.full_name = self.title

        return self
