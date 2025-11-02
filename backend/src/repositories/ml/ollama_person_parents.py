from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.content import Media
from src.interfaces.extractor import IDataMiner
from src.repositories.ml.ollama_messager import OllamaMessager
from src.settings import MLSettings


class ParentsTradesExctractor(IDataMiner, OllamaMessager):
    """
    TODO:
    - remove this code
    """

    def __init__(self, settings: MLSettings):

        self.model = settings.ollama_llm_model

    def extract_entity(
        self,
        content: str,
        media: list[Media],
        entity_type: EntityComponent,
        parent: Composable | None = None,
    ) -> EntityComponent:

        prompt = f"""
            Context: {content}
            Question: Quel était le métier des parents ? Réponds de façon concise, si tu ne sais pas, n'invente pas de données.
            Réponse:"""

        return self.request_entity(
            prompt=prompt,
            entity_type=entity_type,
            parent=parent,
        )
