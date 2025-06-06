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
