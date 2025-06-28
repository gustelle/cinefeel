from loguru import logger

from src.entities.source import SourcedContentBase, Storable
from src.repositories.ml.ollama_visioner import OllamaVisioner
from src.settings import Settings


class PersonVisualAnalysis(OllamaVisioner):

    def __init__(self, settings: Settings):

        self.model = settings.vision_model

    def extract_entity(
        self,
        content: str,
        entity_type: Storable,
        base_info: SourcedContentBase,
    ) -> Storable:

        prompt = """
            S'agit-il d'une personne ? 
            si oui, quelle est la couleur de sa peau ?
            est-elle obèse ? 
            est-elle naine ?
            est-elle handicapée ?
        """

        logger.debug(f"Extracting info from : {content[:100]}...")

        return self.analyze_image_using_prompt(
            prompt=prompt,
            entity_type=entity_type,
            image_path=content,
        )
