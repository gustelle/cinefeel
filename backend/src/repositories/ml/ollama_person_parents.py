from loguru import logger

from src.entities.content import Media
from src.entities.source import SourcedContentBase, Storable
from src.repositories.ml.ollama_dataminer import OllamaDataMiner
from src.settings import Settings


class ParentsTradesExctractor(OllamaDataMiner):

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
            Question: Quel était le métier des parents de '{base_info.title}' ? Réponds de façon concise, si tu ne sais pas, n'invente pas de données.
            Réponse:"""

        logger.debug(f"Extracting parents trades from content: {content[:100]}...")

        return self.parse_entity_from_prompt(
            prompt=prompt,
            entity_type=entity_type,
        )
