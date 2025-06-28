import ollama
from loguru import logger
from pydantic import BaseModel

from src.entities.extraction import ExtractionResult
from src.entities.source import Storable
from src.interfaces.extractor import IDataMiner

from .response_formater import create_response_model


class OllamaDataMiner(IDataMiner):
    """
    Abstract class for LLM data miners.
    """

    model: str
    prompt: str

    def parse_entity_from_prompt(
        self, prompt: str, entity_type: Storable
    ) -> ExtractionResult:

        try:

            score = 0.0
            result: BaseModel | None = None

            response_model = create_response_model(entity_type)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                format=response_model.model_json_schema(),
                options={
                    # Set temperature to 0 for more deterministic responses
                    "temperature": 0
                },
            )

            msg = response.message.content

            # isolate the score and the entity from the response
            dict_resp = response_model.model_validate_json(
                msg,
            ).model_dump(
                mode="json",
                exclude_none=True,
            )

            # pop the score from the values
            score = dict_resp.pop("score")

            # ensure score is between 0.0 and 1.0
            # sometimes the model returns a score like 1.0000000000000002
            score = max(0.0, min(score, 1.0))

            # the entity is the remaining values
            result = entity_type.model_validate(dict_resp)

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise ValueError(f"Error parsing response: {e}") from e

        return ExtractionResult[entity_type](score=score, entity=result)
