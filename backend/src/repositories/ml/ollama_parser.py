import ollama
from loguru import logger
from pydantic import BaseModel, Field

from src.entities.film import Film
from src.entities.person import Person
from src.entities.woa import WOAType
from src.interfaces.content_parser import IContentParser
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


class OllamaParser[T: Film | Person](IContentParser[T]):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    model: str
    questions: list[LLMQuestion]
    entity_type: type[T]

    def __init__(self, settings: Settings = None):

        self.model = settings.llm_model
        self.questions = settings.llm_questions

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type

        return new_cls

    def resolve(self, content: str) -> T:
        """
        Transform the given content into an entity of type T.

        TODO:
        - Ability to complete an entity

        Args:
            content (str): The content to parse, typically a string containing text.

        Returns:
            T: An instance of the entity type T, such as Film or Person, containing the parsed data.
            Raises ValueError if parsing fails or if the content is not relevant.

        Raises:
            ValueError: If the content cannot be parsed into an entity of type T.
        """

        result: T | None = None

        for question in self.questions:

            if question.content_type != self.entity_type.__name__.lower():
                continue

            logger.debug(f"Processing question: {question.question}")

            prompt = f"Context: {content}\n\nQuestion: {question}\nRéponse:"

            if result is None:
                # case where the entity needs to be created
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    format=self.entity_type.model_json_schema(),
                    options={
                        # Set temperature to 0 for more deterministic responses
                        "temperature": 0
                    },
                )

                msg = response.message.content

                try:

                    result = self.entity_type.model_validate_json(msg)

                    if issubclass(self.entity_type, Film):
                        # set the uid to the work of art id
                        result.woa_type = WOAType.FILM

                except Exception as e:
                    raise ValueError(f"Error parsing response: {e}") from e
            else:
                # case where the entity already exists and we want to complete it
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    format=question.response_format,
                    options={
                        # Set temperature to 0 for more deterministic responses
                        "temperature": 0
                    },
                )

                msg = response.message.content

                try:
                    logger.debug(f"Response from LLM: {msg}")
                except Exception as e:
                    raise ValueError(f"Error parsing response: {e}") from e

        return result
