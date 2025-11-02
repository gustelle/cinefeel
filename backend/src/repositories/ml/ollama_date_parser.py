from src.interfaces.formatter import IFormatter
from src.repositories.ml.ollama_messager import OllamaMessager
from src.settings import MLSettings


class OllamaDateFormatter(IFormatter, OllamaMessager):

    def __init__(self, settings: MLSettings):

        self.model = settings.ollama_llm_model

    def format(
        self,
        content: str,
    ) -> str:

        prompt = f"""
            Question: Le texte suivant contient une date: '{content}', mets la au format ISO 8601.
            Réponse:"""

        return self.request_formatted(
            prompt=prompt,
        )
