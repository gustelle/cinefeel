from typing import get_args, get_origin

from loguru import logger
from mistralai import Mistral
from pydantic import BaseModel, Field, HttpUrl, create_model
from typing_inspection.introspection import (
    AnnotationSource,
    inspect_annotation,
    is_union_origin,
)

from src.entities.content import Media
from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import IDataMiner
from src.settings import Settings

#


class MistralDataMiner(IDataMiner):
    """
    Mistral Data Miner is a wrapper around the Mistral API for data extraction.
    """

    def __init__(self, settings: Settings):
        """
        Initializes the MistralDataMiner with the provided settings.

        Args:
            settings: The settings object containing configuration for the data miner.
        """
        self.settings = settings

    def _is_expected_in_response(self, k: str, annotation: AnnotationSource) -> bool:
        """
        some types are not expected in the response, like HttpUrl,
        because the LLM usually provides crappy URLs that are not valid, which invalidates the model.

        Args:
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

    def create_response_model(self, entity_type: BaseModel) -> type[BaseModel]:
        """
        Dynamically create a Pydantic model for the response based on the entity type.

        This is motivated by the needs:
        - to have a score field in the response model, which is not part of the entity type.
        - to exclude fields expected as HttpUrl, which will be patched later, because the LLM does not know the URLs of the sources.

        Args:
            entity_type (BaseModel): The type of entity to create a response model for.

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
                if self._is_expected_in_response(k, v.annotation)
            },
        )

    def extract_entity(
        self,
        content: str,
        _: list[Media],
        entity_type: BaseModel,
        base_info: SourcedContentBase,
    ) -> ExtractionResult:
        """
        Transform the given content into an entity of type T.

        Args:
            content (str): The content to parse, typically a string containing text.
            media (list[Media]): A list of Media objects associated with the content.
            entity_type (BaseModel): The type of entity to create from the content.
                This should be a Pydantic model that defines the structure of the entity.
            base_info (SourcedContentBase): Base information to provide context to the LLM,
                this avoids hallucinations and helps the model to focus on the right context.

        Returns:
            ExtractionResult: An instance of ExtractionResult containing:
                - score: A float representing the confidence score of the extraction.
                - entity: An instance of the entity type T, populated with the extracted data.

        Raises:
            ValueError: If the content cannot be parsed into an entity of type T.
        """

        score = 0.0
        result: BaseModel | None = None

        response_model = self.create_response_model(entity_type)

        prompt = f"""
            Context: {content}
            Question: Dans cet extrait, donne-moi des informations sur {base_info.title}, réponds de façon concise, si tu ne sais pas, n'invente pas de données.
            Réponse:"""

        client = Mistral(api_key=self.settings.mistral_api_key)

        messages = [{"role": "user", "content": prompt}]
        chat_response = client.chat.complete(
            model="mimistral-medium-latest",
            messages=messages,
            temperature=0.0,
            response_format=response_model.model_json_schema(),
        )

        logger.debug(f"Response from Mistral: {chat_response}")

        msg = chat_response.message.content

        try:

            # isolate the score and the entity from the response
            dict_resp = response_model.model_validate_json(
                msg,
            ).model_dump(
                mode="json",
                exclude_none=True,
            )

            # pop the score from the values
            score = dict_resp.pop("score")

            # ensure score is between 0.0 and 1.0
            # sometimes the model returns a score like 1.0000000000000002
            score = max(0.0, min(score, 1.0))

            # the entity is the remaining values
            result = entity_type.model_validate(dict_resp)

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise ValueError(f"Error parsing response: {e}") from e

        return ExtractionResult[entity_type](score=score, entity=result)
