import ollama
from pydantic import BaseModel, Field

from src.interfaces.extractor import IContentExtractor
from src.settings import Settings


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
    question: str

    def __init__(self, settings: Settings):

        self.model = settings.llm_model
        self.question = settings.llm_question

    def extract_entity[T](self, content: str, entity_type: BaseModel) -> T:
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

        prompt = f"Context: {content}\n\nQuestion: {self.question}\nRéponse:"

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
            format=entity_type.model_json_schema(by_alias=True),
            options={
                # Set temperature to 0 for more deterministic responses
                "temperature": 0
            },
        )

        msg = response.message.content

        try:

            result = entity_type.model_validate_json(msg, by_alias=True)

        except Exception as e:
            raise ValueError(f"Error parsing response: {e}") from e

        return result
