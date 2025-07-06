from typing import get_args, get_origin

from pydantic import BaseModel, Field, HttpUrl, create_model
from typing_inspection.introspection import (
    AnnotationSource,
    inspect_annotation,
    is_union_origin,
)

from src.entities.component import EntityComponent


def _is_expected_in_response(k: str, annotation: AnnotationSource) -> bool:
    """
    some fields or field types are not expected in the response, like `HttpUrl`, or the `uid` field,
    which is not part of the entity type, but is used to identify the entity in the database.
    This is also the case for `HttpUrl` fields, which are not expected in
    because the LLM usually provides crappy URLs that are not valid, which invalidates the model.

    Args:
        k (str): The name of the field to inspect
        annotation (AnnotationSource): The type annotation to inspect.

    Returns:
        bool: True if the type should be kept, False if it should be excluded.
    """
    excluded_types = (HttpUrl, list[HttpUrl], set[HttpUrl])

    excluded_fields = (
        # optionnally, we could exclude fields here, like `uid`
        # but in this case, be careful to validation if the field is required
    )

    if k in excluded_fields:
        return False

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


def create_response_model(entity_type: EntityComponent) -> type[BaseModel]:
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

    # if the entity_type is not a Pydantic model,
    # assign the type to a BaseModel with a single field for the score
    if not hasattr(entity_type, "__pydantic_fields__"):
        raise TypeError(
            f"Expected a Pydantic model, but got {entity_type.__name__}. "
            "Please ensure the entity_type is a subclass of Pydantic's BaseModel."
        )

    return create_model(
        "LLMResponse",
        score=(
            float,
            Field(
                # default=0.0,
                # ge=0.0,
                # le=1.0,  # it can happen that the model return a score like 1.0000000000000002
                description="Confidence score of the extracted data, between 0.0 and 1.0.",
                # examples=[0.95, 0.85, 0.75],
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
