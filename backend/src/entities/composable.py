from typing import Self

from loguru import logger
from pydantic import BaseModel, TypeAdapter, ValidationError

from src.entities.extraction import ExtractionResult


class Composable(BaseModel):
    """
    Represents a composable entity that can be used to build complex structures.
    This class is designed to be extended by other classes that require composability.
    It provides a base structure for entities that can be composed together.
    """

    @classmethod
    def construct(
        cls, parts: list[ExtractionResult], by_alias: bool = False, **kwargs
    ) -> Self:
        """
        inner method to compose this entity with other entities or data.
        should not be called directly, use `from_parts` when calling from outside.

        in case several parts for the same entity are provided:
        - if the inner fields are complementary, we merge them
        - if the inner fields are conflicting, we keep the one with the highest score

        Example:
            ```python
            composed_entity = Composable.from_parts(base_info, parts)
            ```

        Args:
            base_info (SourcedContentBase): Base information including title, permalink, and uid.
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.
            by_alias (bool): Whether to use field aliases for composition.
            kwargs: Additional keyword arguments for the composition.

        Returns:
            Composable: A new instance of the composed entity.
        """
        _fields = kwargs

        _scored_parts = {}

        for part in parts:

            for k, v in cls.model_fields.items():

                try:

                    _is_set = False

                    # 1st try to set as a list
                    try:
                        valid_entity = TypeAdapter(v.annotation).validate_python(
                            [part.entity], by_alias=by_alias
                        )

                        # check if the field is already set and has better score
                        if k in _scored_parts:
                            if _scored_parts[k] >= part.score:
                                logger.debug(
                                    f"Skipping part with lower score for field '{k}': {part.score} < {_scored_parts[k]}"
                                )
                                continue

                        if _fields.get(k, None) is not None and isinstance(
                            _fields[k], list
                        ):
                            _fields[k].extend(valid_entity)
                        else:
                            _fields[k] = valid_entity

                        _is_set = True
                    except (ValidationError, TypeError, AttributeError):

                        # else try to set as a single entity
                        valid_entity = TypeAdapter(v.annotation).validate_python(
                            part.entity, by_alias=by_alias
                        )

                        # check if the field is already set and has better score
                        if k in _scored_parts:
                            if _scored_parts[k] >= part.score:
                                logger.debug(
                                    f"Skipping part with lower score for field '{k}': {part.score} < {_scored_parts[k]}"
                                )
                                continue

                        _fields[k] = valid_entity

                        _is_set = True
                    finally:
                        if _is_set:

                            logger.debug(
                                f"Set field '{k}' with entity: {valid_entity} and score: {part.score}"
                            )
                            _scored_parts[k] = part.score
                            break
                except (ValidationError, AttributeError, TypeError):
                    pass

        logger.debug(
            f"scored_parts: {[(str(ent), score) for ent, score in _scored_parts.items()]}"
        )

        logger.debug(f"fields: {_fields}")
        logger.debug(f"using by_alias={by_alias}")

        return cls.model_validate(_fields, by_alias=by_alias)

    @classmethod
    def from_parts(cls, base_info: BaseModel, parts: list[ExtractionResult]) -> Self:
        """
        Compose this entity with other entities or data.

        Args:
            base_info (BaseModel): Base information including title, permalink, and uid.
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.

        Returns:
            Composable: A new instance of the composed entity.
        """
        raise NotImplementedError(
            f"{cls.__name__}.from_parts() must be implemented in subclasses."
        )
