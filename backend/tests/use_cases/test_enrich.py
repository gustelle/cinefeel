# Run the use case

from pathlib import Path

import pytest

from src.settings import Settings
from src.use_cases.serve import ServeUseCase

_local_dir = Path(__file__).parent.resolve()


@pytest.mark.skip(reason="end-to-end test that requires a running Prefect server.")
def test_uc_enrich(
    test_db_settings: Settings,
):
    """
    End-to-end test on Georges Méliès
    """
    # given

    local_db_path = _local_dir / ".db"

    settings = test_db_settings.model_copy(
        update={
            "persistence_directory": "/Users/guillaume/Dev/cinefeel/backend/data",
            "db_path": local_db_path
            / "test.db",  # Use the local directory for the database
        }
    )
    use_case = ServeUseCase(settings=settings)

    use_case.execute()

    # If no exceptions are raised, the test passes
    assert True

    # remove the created files after the test
    local_db_path.unlink(missing_ok=True)
