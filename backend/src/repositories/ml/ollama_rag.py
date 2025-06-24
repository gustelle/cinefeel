from src.entities.source import SourcedContentBase, Storable
from src.repositories.ml.ollama_dataminer import OllamaDataMiner
from src.settings import Settings


class OllamaRAG(OllamaDataMiner):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    def __init__(self, settings: Settings):

        self.model = settings.llm_model

    def extract_entity(
        self,
        content: str,
        entity_type: Storable,
        base_info: SourcedContentBase,
    ) -> Storable:

        prompt = f"""
            Context: {content}
            Question: Dans cet extrait, donne-moi des informations sur {base_info.title}, réponds de façon concise, si tu ne sais pas, n'invente pas de données.
            Réponse:"""

        return self.parse_entity_from_prompt(
            prompt=prompt,
            entity_type=entity_type,
        )
