from pydantic import BaseModel, Field

from src.entities.source import Storable


class ExtractionResult[T: Storable](BaseModel):
    """
    Base class for extracted entities.
    This class can be extended to define specific types of entities.
    """

    score: float = Field(
        default=0.0,
        description="Confidence score about the information extracted from the content.",
        ge=0.0,  # lowest score
        le=1.0,  # highest score
    )
    entity: T

    resolve_as: type[T] | None = Field(
        default=None,
        description="Optional type to resolve the extracted entity as. "
        "This is useful when you want to force resolution to a specific type.",
    )
