
from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.content import Media
from src.interfaces.extractor import IDataMiner
from src.repositories.ml.ollama_messager import OllamaMessager
from src.settings import Settings


class GenericOllamaExtractor(IDataMiner, OllamaMessager):
    """
    OllamaChat is a wrapper around the Ollama API for chat-based interactions with language models.
    """

    def __init__(self, settings: Settings):

        self.model = settings.ollama_llm_model

    def extract_entity(
        self,
        content: str,
        media: list[Media],
        entity_type: EntityComponent,
        parent: Composable | None = None,
    ) -> EntityComponent:

        # logger.info(f"Extracting '{entity_type}'")
        # logger.info(f"{content[:200]}...")

        prompt = f"""
            Context: {content}
            Question: Extract the relevant information, do not invent data if not present in the context.
            Réponse:"""

        return self.request_entity(
            prompt=prompt,
            entity_type=entity_type,
            parent=parent,
        )
