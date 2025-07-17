import pytest

from src.settings import Settings


@pytest.fixture(scope="module")
def test_db_settings():

    yield Settings(
        db_persistence_directory=None,  # Use in-memory database for testing
        db_max_size=1 * 1024 * 1024 * 1024,  # 1 GB for testing
    )
