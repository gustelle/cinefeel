from src.entities.content import Media
from src.entities.source import SourcedContentBase, Storable
from src.repositories.ml.ollama_dataminer import OllamaDataMiner
from src.settings import Settings


class InfluenceExtractor(OllamaDataMiner):
    """
    specialized extractor for WOAInfluence
    """

    def __init__(self, settings: Settings):

        self.model = settings.llm_model

    def extract_entity(
        self,
        content: str,
        media: list[Media],
        entity_type: Storable,
        base_info: SourcedContentBase,
    ) -> Storable:

        prompt = f"""
            Context: {content}
            Question: Quelles sont les influences de '{base_info.title}' ? Réponds de façon concise, si tu ne sais pas, n'invente pas de données.
            Réponse:"""

        return self.parse_entity_from_prompt(
            prompt=prompt,
            entity_type=entity_type,
        )
