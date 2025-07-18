import ollama
from loguru import logger
from pydantic import BaseModel

from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.ml import ExtractionResult, FormattedResult
from src.interfaces.llm import ILLM

from .response_formater import create_response_model


class OllamaMessager(ILLM):

    model: str
    prompt: str

    def request_entity(
        self,
        prompt: str,
        entity_type: EntityComponent,
        parent: Composable | None = None,
    ) -> ExtractionResult:
        """
        sends a request to the Ollama model to extract an entity from the provided prompt.
        """

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
                exclude_unset=True,
            )

            # pop the score from the values
            score = dict_resp.pop("score", 0)

            # ensure score is between 0.0 and 1.0
            # sometimes the model returns a score like 1.0000000000000002
            score = max(0.0, min(score, 1.0))

            if parent is not None:
                dict_resp["parent_uid"] = parent.uid

            # the entity is the remaining values
            result = entity_type.model_validate(dict_resp)

            logger.debug(
                f"Response from Ollama: {result.model_dump_json(indent=2, exclude_none=True, exclude_unset=True)}"
            )

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise ValueError(f"Error parsing response: {e}") from e

        return ExtractionResult(score=score, entity=result)

    def request_formatted(self, prompt: str) -> FormattedResult:

        try:

            logger.debug(f"Requesting formatted response with prompt: {prompt}")

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={
                    # Set temperature to 0 for more deterministic responses
                    "temperature": 0
                },
            )

            return response.message.content.strip()

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise ValueError(f"Error parsing response: {e}") from e
