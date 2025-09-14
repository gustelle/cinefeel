from pydantic import BaseModel, Field

from src.entities.component import EntityComponent


class MLScoredData(BaseModel):
    """
    Base class for data used in machine learning models.
    This class can be extended to include specific data types.
    """

    score: float = Field(
        default=0.0,
        description="Confidence score about the information extracted from the content.",
        ge=0.0,  # lowest score
        le=1.0,  # highest score
    )


class ExtractionResult(MLScoredData):
    """
    The result of an extraction operation done by a machine learning model.
    """

    entity: EntityComponent = Field(
        ...,
        description="The extracted entity",
    )

    resolve_as: type[EntityComponent] | None = Field(
        default=None,
        description="Optional type to resolve the extracted entity as. "
        "This is useful when you want to force resolution to a specific type.",
    )


class FormattedResult(BaseModel):
    """
    ML may be used to format data, e.g. a date in a specific format.
    So a FormattedResult is a simple wrapper around the formatted string.

    Example: we may request to format the date `Wednesday 21` as `21/03/2024`.
    """

    formatted: str = Field(
        ...,
        description="The formatted result of the extraction.",
    )
