import ollama

from src.entities.film import Film
from src.entities.person import Person
from src.entities.woa import WOAType
from src.interfaces.content_parser import IContentParser
from src.settings import Settings


class OllamaParser[T: Film | Person](IContentParser[T]):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    model: str
    question: str

    def __init__(self, settings: Settings = None):

        self.model = settings.llm_model
        self.question = settings.llm_question

    def resolve(self, content: str) -> T:
        """
        Transform the given content into an entity of type T.
        """

        # https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        entity_type: T = self.__orig_class__.__args__[0]

        prompt = f"Context: {content}\n\nQuestion: {self.question}\nAnswer:"

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

            ent = entity_type.model_validate_json(msg)

            if issubclass(entity_type, Film):
                # set the uid to the work of art id
                ent.woa_type = WOAType.FILM

            return ent

        except Exception as e:
            raise ValueError(f"Error parsing response: {e}") from e
