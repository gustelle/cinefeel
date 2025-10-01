from __future__ import annotations

from typing import Any, Self

from loguru import logger
from pydantic import (
    ConfigDict,
    Field,
    HttpUrl,
    TypeAdapter,
    ValidationError,
    model_validator,
)
from slugify import slugify

from src.entities.base import Identifiable
from src.entities.component import EntityComponent
from src.entities.ml import ExtractionResult


class Composable(Identifiable):
    """
    An entity that is made up of several parts that can be composed together.
    """

    model_config = ConfigDict(
        validate_assignment=True,  # re-validate the model when assigning values
        use_enum_values=True,  # use the enum values instead of the enum instances
    )

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

    @model_validator(mode="before")
    @classmethod
    def assign_uid(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        UID assignment is crucial for the entity merging process.
        It is important to control how the UID is generated
        """

        if not data.get("title", None):
            raise ValueError("Title is required to generate UID.")

        data["uid"] = f"{cls.__name__}:{slugify(data.get("title"))}"

        return data

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

        for part in parts:

            # only parts that are directly related to the entity
            # are considered for composition
            if part.entity is not None and part.entity.parent_uid != uid:
                logger.warning(
                    f"Skipping part with UID '{part.entity.uid}' "
                    f"because it is not related to the entity with UID '{uid}'."
                )
                continue

            for root_field_name, root_field_definition in cls.model_fields.items():

                logger.trace(
                    f"Processing field '{root_field_name}' of type '{root_field_definition.annotation}'"
                )

                # fetch the field correctly from `extraction_result`,
                # merging the field values if it is already populated
                _valid_value = cls._validate_as_type(
                    extraction_result=part,
                    field_type=root_field_definition.annotation,
                )

                # save the best score for the field
                if _valid_value is not None:

                    new_value = cls._get_field_value(
                        initial_value=populated_entities.get(root_field_name, None),
                        candidate_value=_valid_value,
                    )

                    populated_entities[root_field_name] = new_value

                    break

        logger.debug(
            f"Populated entities before final validation: {populated_entities}"
        )

        # re-pass through the model validation
        # to ensure all fields are correctly populated
        # and to ensure the UID is correctly assigned
        v = cls.model_validate(populated_entities, by_alias=False, by_name=True)

        logger.debug("_" * 80)
        logger.debug(f"Composed '{cls.__name__}'")
        logger.debug(v.model_dump_json(indent=2))
        logger.debug("-" * 80)

        return v

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
            e = TypeAdapter(field_type).validate_python(
                [entity],
            )

            # save score for each item in the list
            item: EntityComponent
            for item in e:
                item.score = extraction_result.score
            return e

        except ValidationError:

            # 3. case where the entity is not valid as a list
            # we try to validate it as a single item
            try:
                e: EntityComponent = TypeAdapter(field_type).validate_python(
                    entity,
                )
                # save the score for the single entity
                e.score = extraction_result.score
                return e
            except ValidationError:
                pass

            return None

    @staticmethod
    def _get_field_value(
        initial_value: EntityComponent | list[EntityComponent] | None,
        candidate_value: EntityComponent | list[EntityComponent],
    ) -> EntityComponent | list[EntityComponent]:
        """
        Populate the value of the field with the extraction result.

        Args:
            initial_value (EntityComponent | list[EntityComponent]): The initial value of the field.
            candidate_value (EntityComponent | list[EntityComponent]): The new value to be assigned to the field.

        Returns:
            EntityComponent | list[EntityComponent]: The updated value of the field.
        """
        new_value = initial_value

        if isinstance(candidate_value, list):

            # 1. case where the field is a list
            if new_value is not None and isinstance(new_value, list):
                new_value.extend(candidate_value)

            else:
                # 2. case where the field is not set
                new_value = candidate_value

        elif new_value is not None and isinstance(new_value, EntityComponent):
            new_value = new_value.update(candidate_value)

        else:
            # 3. case where the field is not set
            new_value = candidate_value

        return new_value
