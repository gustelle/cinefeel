import datetime

import isodate
from loguru import logger
from pydantic import Field, create_model

from src.repositories.ml.ollama_dataminer import OllamaDataMiner
from src.settings import Settings


class OllamaDateFormatter(OllamaDataMiner):

    def __init__(self, settings: Settings):

        self.model = settings.llm_model

    def format(
        self,
        content: str,
    ) -> str:

        prompt = f"""
            Question: Le texte suivant contient une date: '{content}', mets la au format ISO 8601.
            Réponse:"""

        # generate a dynamic model for the date entity
        entity_type = create_model(
            "DateEntity",
            value=(
                datetime.date,
                Field(
                    ...,
                    description="La date au format ISO 8601.",
                    examples=["2023-03-15", "2022-12-01"],
                ),
            ),
        )

        result = self.parse_entity_from_prompt(
            prompt=prompt,
            entity_type=entity_type,
        )

        if result and result.entity and result.entity.value:
            return result.entity.value.isoformat()

        return None


class OllamaDurationFormatter(OllamaDataMiner):

    def __init__(self, settings: Settings):

        self.model = settings.llm_model

    def format(
        self,
        content: str,
    ) -> float | None:
        """
        Formats a duration string into ISO 8601 format

        """

        prompt = f"""
            Question: Le texte suivant contient une durée: '{content}', mets la au format ISO 8601.
            Réponse:"""

        # generate a dynamic model for the duration entity
        entity_type = create_model(
            "DurationEntity",
            value=(
                datetime.timedelta,
                Field(
                    ...,
                    description="La durée au format ISO 8601.",
                    examples=["PT1H30M", "PT2H15M30S", "PT1M20S"],
                ),
            ),
        )

        result = self.parse_entity_from_prompt(
            prompt=prompt,
            entity_type=entity_type,
        )

        if result and result.entity and result.entity.value:
            logger.debug(
                f"Parsed duration: {result.entity.value.total_seconds()} seconds"
            )
            return isodate.duration_isoformat(result.entity.value)

        return None
