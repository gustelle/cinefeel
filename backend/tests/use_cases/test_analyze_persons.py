# Run the use case
import asyncio
from pathlib import Path

from src.settings import Settings, WikiTOCPageConfig
from src.use_cases.analyze_persons import WikipediaPersonAnalysisUseCase

_local_dir = Path(__file__).parent.resolve()


def test_uc_person():
    """
    End-to-end test for the WikipediaPersonAnalysisUseCase.
    This test runs the use case and checks if it completes without errors.
    """
    # given
    mediawiki_start_pages = [
        WikiTOCPageConfig(
            page_id="Liste_de_films_français_sortis_en_1907",  # Example page ID for Douglas Adams
            toc_content_type="person",
            toc_css_selector=".wikitable td:nth-child(2) [title='Georges Méliès']",
        )
    ]
    settings = Settings(
        persistence_directory=_local_dir / "data",
        mediawiki_start_pages=mediawiki_start_pages,
    )
    use_case = WikipediaPersonAnalysisUseCase(settings=settings)

    asyncio.run(use_case.execute())

    # If no exceptions are raised, the test passes
    assert True
