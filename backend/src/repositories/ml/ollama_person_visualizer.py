import tempfile

import httpx
from loguru import logger

from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.content import Media
from src.repositories.ml.ollama_visioner import OllamaVisioner
from src.settings import Settings


class PersonVisualAnalysis(OllamaVisioner):

    def __init__(self, settings: Settings):

        self.model = settings.vision_model

    def extract_entity(
        self,
        content: str,
        media: list[Media],
        entity_type: EntityComponent,
        parent: Composable | None = None,
    ) -> EntityComponent:

        # take the first media item of type image
        if not media or not any(m.media_type == "image" for m in media):
            raise ValueError("No image media found in the provided media list.")

        media = [m for m in media if m.media_type == "image"]

        # store the image temporarily
        with tempfile.NamedTemporaryFile() as temp:

            # download the image if it's a URL and store it locally temporarily
            # using httpx for downloading
            response = httpx.get(str(media[0].src), follow_redirects=True, timeout=1)

            if not response.is_success:
                raise ValueError(f"Failed to download image from {media[0].src}")

            temp.write(response.content)
            temp.flush()

            prompt = """
                S'agit-il d'une personne ? 
                si oui, quelle est la couleur de sa peau ?
                est-elle obèse ? 
                est-elle naine ?
                est-elle handicapée ?
                Décrit le genre de la personne (homme, femme, autre).
                S'il ne s'agit pas d'une personne, ne pas répondre à ces questions.
            """

            r = self.analyze_image_using_prompt(
                prompt=prompt,
                entity_type=entity_type,
                image_path=temp.name,
            )

            logger.debug(f"Visual analysis result: {r.model_dump_json(indent=2)}")

            return r
