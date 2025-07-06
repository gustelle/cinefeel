from __future__ import annotations

import re
from typing import Any, Self

from loguru import logger
from pydantic import (
    Field,
    HttpUrl,
    TypeAdapter,
    ValidationError,
    model_validator,
)
from unidecode import unidecode

from src.entities.base import Identifiable
from src.entities.component import EntityComponent
from src.entities.ml import ExtractionResult


class Composable(Identifiable):
    """
    An entity that is made up of several parts that can be composed together.
    """

    title: str = Field(
        ...,
        description="The title of the information entity.",
        examples=["Stanley Kubrick", "The Shining"],
    )

    permalink: HttpUrl = Field(
        ...,
        description="The permalink to the object, typically a URL.",
        examples=[
            "https://fr.wikipedia.org/wiki/Stanley_Kubrick",
        ],
    )

    @model_validator(mode="after")
    def assign_uid(self) -> Self:
        """
        UID assignment is crucial for the entity merging process.
        It is important to control how the UID is generated
        """

        # replace accents and casefold to lowercase
        value = unidecode(self.title).casefold()

        # constraint of meili:
        # only (a-z A-Z 0-9), hyphens (-) and underscores (_) are allowed
        value = re.sub(r"[^a-z0-9_-]", "", value, flags=re.IGNORECASE)

        # remove quotes
        value = value.replace('"', "").replace("'", "")

        self.uid = value

        return self

    @classmethod
    def compose(
        cls,
        uid: str,
        title: str,
        permalink: str | HttpUrl,
        parts: list[ExtractionResult],
        **kwargs,
    ) -> Self:
        """
        Compose this entity with other entities or data.

        in case several parts for the same entity are provided:
        - if the inner fields are complementary, we merge them
        - if the inner fields are conflicting, we keep the one with the highest score

        **Only parts that are located at the root of the target entity
        are considered for composition**. This means that the entity must be
        directly assignable to the field in the model.

        Args:
            title (str): The title of the composed entity.
            permalink (str | HttpUrl): The permalink to the composed entity.
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.
            kwargs: Additional keyword arguments for the composition.

        Returns:
            Composable: A new instance of the composed entity.
        """

        # NOTE
        # we should pre-populate the composable entity with the base_info
        # in particular the UID is essential in the information merging process
        populated_entities = {
            "title": title,
            "permalink": permalink,
        }

        populated_entities.update(kwargs)

        _best_score_for_field: dict[str, float] = {}

        for part in parts:

            # only parts that are directly related to the entity
            # are considered for composition
            if part.entity is not None and part.entity.parent_uid != uid:
                continue

            for root_field_name, root_field_definition in cls.model_fields.items():

                # fetch the field correctly from `extraction_result`,
                # merging the field values if it is already populated
                _valid_value = cls._validate_as_type(
                    extraction_result=part,
                    field_type=root_field_definition.annotation,
                )

                # save the best score for the field
                if _valid_value is not None:

                    new_value = cls._update_value(
                        initial_value=populated_entities.get(root_field_name, None),
                        initial_score=_best_score_for_field.get(root_field_name, 0.0),
                        value=_valid_value,
                        score=part.score,
                    )

                    populated_entities[root_field_name] = new_value
                    _best_score_for_field[root_field_name] = part.score
                    break

        # re-pass through the model validation
        # to ensure all fields are correctly populated
        # and to ensure the UID is correctly assigned
        v = cls.model_validate(populated_entities, by_name=True)

        logger.debug("_" * 80)
        logger.debug(f"Composed '{cls.__name__}'")
        logger.debug(v.model_dump_json(indent=2))
        logger.debug("-" * 80)

        return v

    @classmethod
    def from_parts(cls, base: Composable, parts: list[ExtractionResult]) -> Self:
        """
        Compose this entity with other entities or data.

        TODO:
        - remove

        Args:
            base_info (BaseModel): Base information including title, permalink, and uid.
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.

        Returns:
            Composable: A new instance of the composed entity.
        """
        raise NotImplementedError(
            f"{cls.__name__}.from_parts() must be implemented in subclasses."
        )

    @staticmethod
    def _validate_as_type(
        extraction_result: ExtractionResult,
        field_type: type[Any],
    ) -> list[EntityComponent] | EntityComponent:
        """
        Validate the extraction result as a specific type, either as a single entity or a list of entities.

        Returns:
            list[EntityComponent] | EntityComponent : The valid entity or list of entities to be assigned to the field,
        """

        entity: EntityComponent = extraction_result.entity

        try:

            # this part runs for both cases: single entity or list of entities
            if extraction_result.resolve_as is not None:
                entity = extraction_result.resolve_as(**entity.model_dump())

            # try to validate the entity as a list
            # if a list is expected for the field
            return TypeAdapter(field_type).validate_python(
                [entity],
            )

        except ValidationError:

            # 3. case where the entity is not valid as a list
            # we try to validate it as a single item
            try:
                return TypeAdapter(field_type).validate_python(
                    entity,
                )
            except ValidationError:
                pass

            return None

    @staticmethod
    def _update_value(
        initial_value: EntityComponent | list[EntityComponent] | None,
        initial_score: float,
        value: EntityComponent | list[EntityComponent],
        score: float,
    ) -> EntityComponent | list[EntityComponent]:
        """
        Populate the value of the field with the extraction result.

        Args:
            initial_value (EntityComponent | list[EntityComponent]): The initial value of the field.
            initial_score (float): The score of the initial value.
            value (EntityComponent | list[EntityComponent]): The new value to be assigned to the field.
            score (float): The score of the new value.

        Returns:
            dict[str, Any]: The updated dictionary with the field populated with the component.
        """
        new_value = None

        if isinstance(value, list):

            new_value = initial_value

            # 1. case where a value is already set for the field
            # we must check if the entity is already in the list
            # and eventually complete the list with the new entity
            if new_value is not None and isinstance(new_value, list):

                new_value.extend(value)

            else:
                # 2. case where the field is not set
                new_value = value
        else:
            new_value = EntityComponent.override_or_complete(
                current_component=initial_value,
                current_score=initial_score,
                component=value,
                component_score=score,
            )

        return new_value
