from typing import get_args, get_origin

from pydantic import BaseModel, Field, HttpUrl, create_model
from typing_inspection.introspection import (
    AnnotationSource,
    inspect_annotation,
    is_union_origin,
)

from src.entities.source import Storable


def _is_expected_in_response(k: str, annotation: AnnotationSource) -> bool:
    """
    some types are not expected in the response, like HttpUrl,
    because the LLM usually provides crappy URLs that are not valid, which invalidates the model.

    Args:
        k (str): The name of the field to inspect, may be used for logging or debugging.
        annotation (AnnotationSource): The type annotation to inspect.

    Returns:
        bool: True if the type should be kept, False if it should be excluded.
    """
    excluded_types = (HttpUrl, list[HttpUrl], set[HttpUrl])

    a = inspect_annotation(annotation, annotation_source=AnnotationSource.ANY)

    _is_expected = True

    if is_union_origin(get_origin(annotation)):

        # unpack the union type
        # e.g. Union[str, int] -> (str, int)
        if any(t in excluded_types for t in get_args(a.type)):
            _is_expected = False

    elif a.type in excluded_types:
        _is_expected = False

    return _is_expected


def create_response_model(entity_type: Storable) -> type[BaseModel]:
    """
    Dynamically create a Pydantic model for the response based on the entity type.

    This is motivated by the needs:
    - to have a score field in the response model, which is not part of the entity type.
    - to exclude fields expected as HttpUrl, which will be patched later, because the LLM does not know the URLs of the sources.

    Args:
        entity_type (Storable): The type of entity to create a response model for.

    Returns:
        type[BaseModel]: A Pydantic model class that matches the structure of the entity type.
    """

    return create_model(
        "LLMResponse",
        score=(
            float,
            Field(
                default=0.0,
                # ge=0.0,
                # le=1.0, # it can happen that the model return a score like 1.0000000000000002
                description="Confidence score of the extracted data, between 0.0 and 1.0.",
                examples=[0.95, 0.85, 0.75],
            ),
        ),
        **{
            k: (
                v.annotation,
                Field(
                    default=v.default,
                    alias=v.validation_alias,
                    serialization_alias=v.serialization_alias,
                    description=v.description,
                    default_factory=v.default_factory,
                ),
            )
            for k, v in entity_type.__pydantic_fields__.items()
            if _is_expected_in_response(k, v.annotation)
        },
    )
