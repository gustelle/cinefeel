from loguru import logger
from mistralai import Mistral
from pydantic import BaseModel

from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.content import Media
from src.entities.ml import ExtractionResult
from src.interfaces.extractor import IDataMiner
from src.settings import Settings

from .response_formater import create_response_model


class MistralDataMiner(IDataMiner):
    """
    Mistral Data Miner is a wrapper around the Mistral API for data extraction.
    """

    def __init__(self, settings: Settings):
        """
        Initializes the MistralDataMiner with the provided settings.

        Args:
            settings: The settings object containing configuration for the data miner.
        """
        self.settings = settings

    def extract_entity(
        self,
        content: str,
        media: list[Media],
        entity_type: EntityComponent,
        parent: Composable | None = None,
    ) -> ExtractionResult:
        """
        TODO:
        - test that parent is correctly attached to the entity

        Args:
            content (str): The content to parse, typically a string containing text.
            media (list[Media]): A list of Media objects associated with the content.
            entity_type (Storable): The type of entity to create from the content.
                This should be a Pydantic model that defines the structure of the entity.
            parent (Composable | None): An optional parent Composable object to attach to the extracted entity.

        Returns:
            ExtractionResult: An instance of ExtractionResult containing:
                - score: A float representing the confidence score of the extraction.
                - entity: An instance of the entity type T, populated with the extracted data.

        Raises:
            ValueError: If the content cannot be parsed into an entity of type T.
        """

        score = 0.0
        result: BaseModel | None = None

        response_model = create_response_model(entity_type)

        client = Mistral(api_key=self.settings.mistral_api_key.get_secret_value())

        prompt = f"""
            Context: {content}
            Question: Structure les informations fournies en contexte au format JSON selon le modèle fourni.
            Réponse:"""

        messages = [{"role": "user", "content": prompt}]

        chat_response = client.chat.parse(
            model=self.settings.mistral_llm_model,
            messages=messages,
            temperature=0.0,
            response_format=response_model,
        )

        if not chat_response.choices or not chat_response.choices[0].message:
            raise ValueError("No valid response from Mistral API.")

        msg = chat_response.choices[0].message.content

        try:

            # isolate the score and the entity from the response
            dict_resp = response_model.model_validate_json(
                msg,
            ).model_dump(
                mode="json",
                exclude_none=True,
                exclude_unset=True,
            )

            # pop the score from the values
            score = dict_resp.pop("score")

            # ensure score is between 0.0 and 1.0
            # sometimes the model returns a score like 1.0000000000000002
            score = max(0.0, min(score, 1.0))

            # reattach the parent content if provided
            if parent:
                dict_resp["parent_uid"] = parent.uid
                logger.debug(
                    f"Attaching parent UID '{parent.uid}' to the extracted entity of type '{entity_type.__name__}'."
                )

            # the entity is the remaining values
            result = entity_type.model_validate(dict_resp)

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise ValueError(f"Error parsing response: {e}") from e

        return ExtractionResult(score=score, entity=result)
