import random
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import orjson

from src.entities.content import TableOfContents
from src.settings import (
    AppSettings,
    MLSettings,
    PrefectSettings,
    ScrapingSettings,
    SearchSettings,
    SectionSettings,
    StatsSettings,
    StorageSettings,
)


def test_ScrapingSettings_load_tocs_from_yml():
    # given
    mock_yml_content = """
    - page_id: "Liste_de_films_français_sortis_en_1907"
      link_selector: ".wikitable td:nth-child(1)"
      entity_type: "Movie"
    - page_id: Liste_de_films_français_sortis_en_1907
      inner_links_selector: .wikitable td:nth-child(2)
      entity_type: "Person"
    """
    with patch("builtins.open", mock_open(read_data=mock_yml_content)):
        # when
        start_pages_config = Path("./start-pages-dev.yml")
        settings = ScrapingSettings(config_file=start_pages_config.as_posix())

        # then
        assert all(isinstance(toc, TableOfContents) for toc in settings.start_pages)
        assert len(settings.start_pages) == 2


def test_MLSettings_is_serializable():
    # given
    settings = MLSettings()

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_section_settings_is_serializable():
    # given
    from src.settings import SectionSettings

    settings = SectionSettings()

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_StatsSettings_is_serializable():
    # given
    from src.settings import StatsSettings

    settings = StatsSettings()

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_storage_settings_is_serializable():
    # given
    from src.settings import StorageSettings

    settings = StorageSettings(
        graphdb_uri="bolt://user:password@localhost:7687",
        redis_dsn="redis://localhost:6379/0",
    )

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_PrefectSettings_is_serializable():
    # given
    from src.settings import PrefectSettings

    settings = PrefectSettings()

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_ScrapingSettings_is_serializable():
    # given
    from src.settings import ScrapingSettings

    settings = ScrapingSettings(config_file="./start-pages-dev.yml")

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_AppSettings_is_serializable():
    # given

    settings = AppSettings(
        _env_file=None,
        search_settings=SearchSettings(_env_file=None),
        storage_settings=StorageSettings(
            _env_file=None,
            graphdb_uri="bolt://user:password@localhost:7687",
            redis_dsn="redis://localhost:6379/0",
        ),
        prefect_settings=PrefectSettings(_env_file=None),
        ml_settings=MLSettings(_env_file=None),
        section_settings=SectionSettings(_env_file=None),
        stats_settings=StatsSettings(_env_file=None),
        scraping_settings=ScrapingSettings(
            _env_file=None, config_file="./start-pages-dev.yml"
        ),
    )

    # when
    serialized = orjson.dumps(settings, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized settings should be bytes"


def test_AppSettings_prefixes(monkeypatch):
    from src.settings import AppSettings, StorageSettings

    # given
    random_int = random.randint(1000, 9999)
    random_string = str(random_int)

    # when
    with tempfile.NamedTemporaryFile("w") as temp_yml:

        temp_yml.write(
            """
        - page_id: "Liste_de_films_français_sortis_en_1907"
          link_selector: ".wikitable td:nth-child(1)"
          entity_type: "Movie"
        """
        )
        temp_yml.flush()

        env_vars = {
            "STORAGE_GRAPHDB_URI": f"bolt://user:password@localhost:{random_int}",
            "STORAGE_REDIS_DSN": f"redis://localhost:6379/{random_int}",
            "SEARCH_BASE_URL": f"http://localhost:{random_int}",
            "SEARCH_API_KEY": random_string,
            "PREFECT_FLOWS_CONCURRENCY_LIMIT": random_int,
            "ML_SUMMARY_MODEL": random_string,
            "SECTIONS_MAX_CHILDREN": random_int,
            "STATS_REDIS_DSN": f"redis://localhost:6379/{random_int}",
            # the file must exist for the test to pass
            "SCRAPING_CONFIG_FILE": temp_yml.name,
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        settings = AppSettings(
            _env_file=None,
            search_settings=SearchSettings(_env_file=None),
            storage_settings=StorageSettings(
                _env_file=None,
            ),
            prefect_settings=PrefectSettings(_env_file=None),
            ml_settings=MLSettings(_env_file=None),
            section_settings=SectionSettings(_env_file=None),
            stats_settings=StatsSettings(_env_file=None),
            scraping_settings=ScrapingSettings(
                _env_file=None,
            ),
        )

        # then
        assert settings.storage_settings.graphdb_uri == env_vars["STORAGE_GRAPHDB_URI"]
        assert settings.storage_settings.redis_dsn == env_vars["STORAGE_REDIS_DSN"]
        assert settings.search_settings.base_url == env_vars["SEARCH_BASE_URL"]
        assert settings.search_settings.api_key == env_vars["SEARCH_API_KEY"]
        assert settings.prefect_settings.flows_concurrency_limit == random_int
        assert settings.ml_settings.summary_model == env_vars["ML_SUMMARY_MODEL"]
        assert settings.section_settings.max_children == random_int
        assert settings.stats_settings.redis_dsn == env_vars["STATS_REDIS_DSN"]
        assert (
            settings.scraping_settings.config_file == env_vars["SCRAPING_CONFIG_FILE"]
        )

        for key, _ in env_vars.items():
            monkeypatch.delenv(key)


def test_AppSettings_defaults():

    # when
    settings = AppSettings(
        _env_file=None,
    )

    # then
    assert settings is not None
    assert settings.search_settings is not None
    assert settings.storage_settings is not None
    assert settings.prefect_settings is not None
    assert settings.ml_settings is not None
    assert settings.section_settings is not None
    assert settings.stats_settings is not None
    assert settings.scraping_settings is not None
