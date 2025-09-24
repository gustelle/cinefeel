from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import Field, HttpUrl, StringConstraints, field_validator

from src.entities.color import SkinColor
from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.religion import Religion
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

    full_name: str = Field(
        ...,
    )
    nicknames: list[str] | None = Field(
        None,
    )
    genre: GenderEnum | None = Field(
        None,
        description="homme, femme, non-binaire ou inconnu.",
    )
    nationalities: list[str] | None = Field(
        None,
        description="les nationalités de la personne",
        examples=["français", "américain", "canadien"],
    )
    religion: Religion | None = Field(
        None,
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

    education: list[str] | None = Field(
        None,
        description="Liste des formations de la personne, par exemple 'Harvard University', 'MIT'.",
    )
    childhood_conditions: ChildHoodConditions | None = Field(
        None,
    )

    @field_validator("birth_date", "death_date", mode="before")
    @classmethod
    def load_from_dt(cls, value: Any) -> str | None:
        """case when loading from a datetime.date object
        which occurs when loading from duckdb JSON files
        """

        if isinstance(value, datetime):
            # Convert datetime.time to HH:MM:SS format
            print(f"Converting {value} to ISO 8601 format")
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
    is_dwarf: bool | None = Field(
        None,
        description="Indique si la personne est naine.",
        examples=[True, False],
    )
    is_disabled: bool | None = Field(
        None,
        description="Indique si la personne est handicapée.",
        examples=[True, False],
    )
    gender: GenderEnum | None = Field(
        None,
        description="Le genre de la personne: homme, femme, non-binaire ou inconnu.",
    )


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

    characteristics: PersonCharacteristics | None = Field(
        None,
    )

    influences: list[WOAInfluence] | None = Field(
        None,
    )
