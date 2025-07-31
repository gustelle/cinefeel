from src.repositories.task_orchestration.extraction_pipeline import (
    batch_extraction_flow,
)
from src.settings import Settings


class WikipediaPersonExtractionUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        batch_extraction_flow.serve(
            name="Wikipedia Person Extraction",
            parameters={
                "settings": self.settings,
                "page_links": [
                    p
                    for p in self.settings.mediawiki_start_pages
                    if p.entity_type == "Person"
                ],
            },
        )
