from typing import Self

from loguru import logger
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo

from src.entities.extraction import ExtractionResult
from src.entities.source import Storable


class Composable(BaseModel):
    """
    Represents a composable entity that can be used to build complex structures.
    This class is designed to be extended by other classes that require composability.

    """

    @classmethod
    def construct(cls, parts: list[ExtractionResult], **kwargs) -> Self:
        """
        inner method to compose this entity with other entities or data.
        should not be called directly, use `from_parts` when calling from outside.

        in case several parts for the same entity are provided:
        - if the inner fields are complementary, we merge them
        - if the inner fields are conflicting, we keep the one with the highest score

        Example:
            ```python
            composed_entity = Composable.construct(base_info, parts)
            ```

        Args:
            parts (list[ExtractionResult]): List of ExtractionResult objects containing parts to compose.
            kwargs: Additional keyword arguments for the composition.

        Returns:
            Composable: A new instance of the composed entity.
        """
        _fields = kwargs

        _part_scores: dict[str, float] = {}

        for part in parts:

            for k, v in cls.model_fields.items():

                # try to work with list of entities first
                _valid = cls._fetch_valid_entities(
                    extraction_result=part,
                    field_name=k,
                    field_info=v,
                    populated_entities=_fields,
                    min_score=_part_scores.get(k, 0),
                )

                # try to assign a single entity if the field is not a list
                if _valid is None:
                    _valid = cls._assign_single_entity(
                        extraction_result=part,
                        field_name=k,
                        field_info=v,
                        populated_entities=_fields,
                        min_score=_part_scores.get(k, 0),
                    )

                if _valid is not None:
                    _fields[k] = _valid
                    _part_scores[k] = part.score
                    break

        logger.debug(f"Final fields after processing parts: {_fields}")

        return cls.model_validate(
            _fields,
        )

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

    @staticmethod
    def _fetch_valid_entities(
        extraction_result: ExtractionResult,
        field_name: str,
        field_info: FieldInfo,
        populated_entities: dict[str, Storable | list[Storable]],
        min_score: float,
    ) -> list[Storable] | None:
        """
        Fetch valid entities from the extraction result and assign them to the field.

        May return None if the entity is not valid or cannot be assigned.
        """

        try:

            entity: Storable = extraction_result.entity

            valid_entity = TypeAdapter(field_info.annotation).validate_python(
                [entity],
            )

            # 1. case where a value is already set for the field
            # we must check if the entity is already in the list
            # and eventually complete the list with the new entity
            if populated_entities.get(field_name, None) is not None:

                # case where the entity is a storable, so we can compare by uid
                # --> search for the entity in the list using uid
                _entity_uids = [ent.uid for ent in populated_entities[field_name]]
                if entity.uid in _entity_uids:

                    # if the entity is already in the list, check the score
                    idx = _entity_uids.index(entity.uid)
                    if extraction_result.score <= min_score:

                        populated_entities[field_name][idx] = (
                            Composable._override_or_complete(
                                storable=populated_entities[field_name][idx],
                                candidate=extraction_result,
                            )
                        )

                    else:
                        # replace the entity with the new one
                        populated_entities[field_name][idx] = valid_entity[0]
                else:
                    # if the entity is not in the list, extend the list
                    populated_entities[field_name].append(valid_entity[0])
            else:
                # 2. case where the field is not set
                populated_entities[field_name] = valid_entity

            return populated_entities[field_name]

        except ValidationError:

            return None

    @staticmethod
    def _assign_single_entity(
        extraction_result: ExtractionResult,
        field_name: str,
        field_info: FieldInfo,
        populated_entities: dict[str, Storable | list[Storable]],
        min_score: float,
    ) -> Storable | None:
        """
        Assign a single entity to the field, validating it against the field's type.

        May return None if the entity is not valid
        """
        try:
            entity: Storable = extraction_result.entity

            valid_entity = TypeAdapter(field_info.annotation).validate_python(
                entity,
            )

            valid_entity = Composable._override_or_complete(
                storable=populated_entities.get(field_name),
                candidate=extraction_result,
                min_score=min_score,
            )

            return valid_entity
        except ValidationError:

            return None

    @staticmethod
    def _override_or_complete(
        storable: Storable | None,
        candidate: ExtractionResult,
        min_score: float = 0.0,
    ) -> Storable:
        """
        Override or complete the storable with the extraction result,
        taking into account the score when necessary,
        and proceeding to a fine grained assembly if needed.

        Args:
            storable (Storable | None): The existing storable entity to be updated.
            candidate (ExtractionResult): The candidate extraction result containing the new entity.
            min_score (float): The minimum score required to override the existing storable.

        Returns:
            Storable: The updated or new storable entity.
        """

        if storable is None:
            logger.debug(
                f"Storable is None, creating a new one from candidate {candidate.entity.uid}"
            )
            return candidate.entity

        # exclude case where the candidate and storable do not relate to the same entity
        if storable.uid != candidate.entity.uid:
            logger.debug(
                f"Storable UID {storable.uid} does not match candidate UID {candidate.entity.uid}"
            )
            return storable

        # proceed to a json dump to compare the fields
        storable_json = storable.model_dump(
            mode="python",
            exclude_none=True,
        )
        candidate_json = candidate.entity.model_dump(
            mode="python",
            exclude_none=True,
        )

        for key, value in candidate_json.items():

            if key not in storable_json or storable_json[key] is None:
                storable_json[key] = value
            elif isinstance(value, list) and candidate.score >= min_score:
                # merge lists if both are lists
                current_list = storable_json.get(key, [])
                current_list.extend(value)
                storable_json[key] = list(set(current_list))
            else:
                # if the key is already set and the score is lower, we keep the current value
                if candidate.score >= min_score:
                    storable_json[key] = value

        new_storable = storable.model_construct(
            **storable_json,
        )

        return new_storable
