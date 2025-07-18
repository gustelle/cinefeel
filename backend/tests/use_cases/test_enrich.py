# Run the use case

from pathlib import Path

import pytest

from src.settings import Settings
from src.use_cases.enrich import EnrichmentUseCase

_local_dir = Path(__file__).parent.resolve()


@pytest.mark.e2e
def test_uc_enrich():
    """
    End-to-end test on Georges Méliès
    """
    # given

    local_db_path = _local_dir / ".db"

    settings = Settings(
        persistence_directory="/Users/guillaume/Dev/cinefeel/backend/data",
        db_persistence_directory=local_db_path,
    )
    use_case = EnrichmentUseCase(settings=settings)

    use_case.execute()

    # If no exceptions are raised, the test passes
    assert True

    # remove the created files after the test
    local_db_path.unlink(missing_ok=True)
