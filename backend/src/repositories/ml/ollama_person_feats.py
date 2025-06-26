from src.entities.source import SourcedContentBase, Storable
from src.repositories.ml.ollama_dataminer import OllamaDataMiner
from src.settings import Settings


class PersonFeaturesExtractor(OllamaDataMiner):
    """
    extracts features of a Person entity using Ollama
    """

    def __init__(self, settings: Settings):

        self.model = settings.llm_model

    def extract_entity(
        self,
        content: str,
        entity_type: Storable,
        base_info: SourcedContentBase,
    ) -> Storable:

        # prompt = f"""
        #     Context: {content}
        #     Question: Dans cet extrait, retrouve les caractéristiques de '{base_info.title}' : poids en Kg, taille en cm, couleur de peau, orientation sexuelle et handicaps. Réponds de façon concise, si tu ne sais pas, n'invente pas de données.
        #     Réponse:"""

        return self.parse_entity_from_prompt(
            # prompt=prompt,
            prompt=content,
            entity_type=entity_type,
        )
