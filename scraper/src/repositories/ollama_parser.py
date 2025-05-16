import ollama
from entities.film import Film
from entities.woa import WorkOfArt
from interfaces.content_parser import IContentParser
from settings import Settings


class OllamaParser[T: WorkOfArt](IContentParser):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    def __init__(self, settings: Settings = None):
        self.model = "mistral:latest"

    def to_entity(self, context: str, question: str, temperature: float = 0) -> T:

        # https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        entity_type: T = self.__orig_class__.__args__[0]

        prompt = f"Context: {context}\n\nQuestion: {question}\nAnswer:"

        response = ollama.chat(
            model="mistral:latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=entity_type.model_json_schema(),
            options={
                "temperature": temperature
            },  # Set temperature to 0 for more deterministic
        )

        msg = response.message.content
        print(f"response : '{msg}'")

        return entity_type.model_validate_json(msg)
