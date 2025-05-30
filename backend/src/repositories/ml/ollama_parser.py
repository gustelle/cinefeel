import ollama
from loguru import logger
from pydantic import BaseModel, Field

from src.interfaces.content_parser import IContentExtractor
from src.settings import LLMQuestion, Settings


class LLMResponse(BaseModel):
    """
    Represents a response from the LLM (Language Model).
    Contains the content of the response and the type of content.
    """

    content: str = Field(
        ...,
        description="The content of the response from the LLM.",
    )


class OllamaExtractor(IContentExtractor):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    model: str
    questions: list[LLMQuestion]

    def __init__(self, settings: Settings = None):

        self.model = settings.llm_model
        self.questions = settings.llm_questions

    def resolve(self, content: str, entity_type: BaseModel) -> BaseModel:
        """
        Transform the given content into an entity of type T.

        Args:
            content (str): The content to parse, typically a string containing text.
            entity_type (BaseModel): The type of entity to create from the content.
                This should be a Pydantic model that defines the structure of the entity.

        Returns:
            BaseModel: An instance of the entity type T, populated with data extracted from the content.

        Raises:
            ValueError: If the content cannot be parsed into an entity of type T.
        """

        result: BaseModel | None = None

        question = self.questions[0]

        logger.debug(f"Processing question: {question.question}")

        prompt = f"Context: {content}\n\nQuestion: {question}\nRéponse:"

        # if result is None:
        # case where the entity needs to be created
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=entity_type.model_json_schema(),
            options={
                # Set temperature to 0 for more deterministic responses
                "temperature": 0
            },
        )

        msg = response.message.content

        try:

            result = entity_type.model_validate_json(msg)

        except Exception as e:
            raise ValueError(f"Error parsing response: {e}") from e

        return result
