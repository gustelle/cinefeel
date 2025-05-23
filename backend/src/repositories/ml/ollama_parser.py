import ollama

from src.entities.film import Film
from src.entities.person import Person
from src.entities.woa import WOAType
from src.interfaces.content_parser import IContentParser
from src.settings import Settings


class OllamaParser[T: Film | Person](IContentParser):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    def __init__(self, settings: Settings = None):

        self.model = settings.llm_model

    def to_entity(self, context: str, question: str) -> T:
        """

        Args:
            context (str): _description_
            question (str): _description_
            temperature (float, optional): _description_. Defaults to 0.

        Returns:
            T: _description_
        """

        # https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        entity_type: T = self.__orig_class__.__args__[0]

        prompt = f"Context: {context}\n\nQuestion: {question}\nAnswer:"

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=entity_type.model_json_schema(),
            options={"temperature": 0},  # Set temperature to 0 for more deterministic
        )

        msg = response.message.content

        try:

            woa = entity_type.model_validate_json(msg)

            if issubclass(entity_type, Film):
                # set the uid to the work of art id
                woa.woa_type = WOAType.FILM

            return woa

        except Exception as e:
            raise ValueError(f"Error parsing response: {e}") from e
