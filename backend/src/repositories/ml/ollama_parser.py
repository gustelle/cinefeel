import ollama
from loguru import logger
from pydantic import BaseModel, Field, create_model

from src.interfaces.extractor import ExtractionResult, IContentExtractor
from src.settings import Settings


class OllamaExtractor(IContentExtractor):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.

    TODO:
    - Create a custom LLM specialized on QA about cinema.
    """

    model: str
    question: str

    def __init__(self, settings: Settings):

        self.model = settings.llm_model
        self.question = settings.llm_question

    def create_response_model(self, entity_type: BaseModel) -> type[BaseModel]:
        """
        Dynamically create a Pydantic model for the response based on the entity type.

        This is motivated by the need to have a score field in the response model, which is not part of the entity type.

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
                    ge=0.0,
                    le=1.0,
                    description="Confidence score of the extracted data.",
                ),
            ),
            __base__=entity_type,
        )

    def extract_entity(self, content: str, entity_type: BaseModel) -> ExtractionResult:
        """
        Transform the given content into an entity of type T.

        Args:
            content (str): The content to parse, typically a string containing text.
            entity_type (BaseModel): The type of entity to create from the content.
                This should be a Pydantic model that defines the structure of the entity.

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
            Question: {self.question}
            Réponse:"""

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=response_model.model_json_schema(by_alias=True),
            options={
                # Set temperature to 0 for more deterministic responses
                "temperature": 0
            },
        )

        msg = response.message.content

        try:

            # isolate the score and the entity from the response
            dict_resp = response_model.model_validate_json(
                msg, by_alias=True
            ).model_dump(
                mode="json",
                exclude_none=True,
                by_alias=True,
            )

            # pop the score from the values
            score = dict_resp.pop("score")

            # the entity is the remaining values
            result = entity_type.model_validate(dict_resp, by_alias=True)

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise ValueError(f"Error parsing response: {e}") from e

        return ExtractionResult(score=score, entity=result)
