from src.repositories.task_orchestration.extraction_pipeline import (
    batch_extraction_flow,
)
from src.settings import Settings


class WikipediaFilmExtractionUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        batch_extraction_flow.serve(
            name="Wikipedia Film Extraction",
            parameters={
                "settings": self.settings,
                "entity": "Movie",
            },
        )
