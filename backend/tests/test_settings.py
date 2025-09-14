from pathlib import Path
from unittest.mock import mock_open, patch

from src.entities.content import TableOfContents
from src.settings import Settings


def test_load_tocs_from_yml():
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
        settings = Settings(start_pages_config=start_pages_config)

        # then
        assert all(
            isinstance(toc, TableOfContents) for toc in settings.download_start_pages
        )
        assert len(settings.download_start_pages) == 2
