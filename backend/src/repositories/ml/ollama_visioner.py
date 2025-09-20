import ollama
from loguru import logger
from pydantic import BaseModel

from src.entities.component import EntityComponent
from src.entities.ml import ExtractionResult
from src.interfaces.extractor import IDataMiner

from .response_formater import create_response_model

# TODO:
# go through txtai to capture text from the image
# see https://github.com/neuml/txtai/blob/master/examples/13_Similarity_search_with_images.ipynb


class OllamaVisioner(IDataMiner):

    model: str
    prompt: str

    def analyze_image_using_prompt(
        self,
        prompt: str,
        entity_type: EntityComponent,
        image_path: str,
        parent: EntityComponent | None = None,
    ) -> ExtractionResult:

        score = 0.0
        result: BaseModel | None = None

        logger.debug(prompt)

        response_model = create_response_model(entity_type)

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt, "images": [image_path]}],
            format=response_model.model_json_schema(),
            options={
                # Set temperature to 0 for more deterministic responses
                "temperature": 0
            },
        )

        msg = response.message.content

        try:

            # isolate the score and the entity from the response
            dict_resp = response_model.model_validate_json(
                msg,
            ).model_dump(
                mode="json",
                exclude_none=True,
            )

            # pop the score from the values
            # fix: if the score is not returned, default to 0
            score = dict_resp.pop("score", 0)

            # ensure score is between 0.0 and 1.0
            # sometimes the model returns a score like 1.0000000000000002
            score = max(0.0, min(score, 1.0))

            if parent:
                dict_resp["parent_uid"] = parent.uid
                logger.debug(
                    f"Attaching parent UID '{parent.uid}' to the extracted entity of type '{entity_type.__name__}'."
                )

            # the entity is the remaining values
            result = entity_type.model_validate(dict_resp)

            logger.debug(f"Parsed result: {result}")

        except Exception as e:

            raise ValueError(f"Error parsing response: {e}") from e

        return ExtractionResult(score=score, entity=result)
