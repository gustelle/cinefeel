import zipfile
from pathlib import Path

import pytest
from neo4j import GraphDatabase

from src.entities.film import Film, FilmActor, FilmMedia, FilmSpecifications
from src.entities.person import Biography, GenderEnum, Person, PersonCharacteristics
from src.entities.woa import WOAInfluence, WOAType
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.settings import Settings


@pytest.fixture
def read_beethoven_html() -> str:
    """
    Reads the HTML content of the Beethoven page from the test data directory.

    the file is zipped to save space in the repository.

    Returns:
        str: The HTML content of the Beethoven page.
    """
    current_dir = Path(__file__).parent
    zip_path = current_dir / "wikipedia_html/Ludwig_van_Beethoven.html.zip"

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        files = zip_ref.namelist()
        for file in files:
            if file == "Ludwig_van_Beethoven.html":
                print(f"Extracting {file} from the zip file.")
                with zip_ref.open(file) as html_file:
                    return html_file.read().decode("utf-8")


@pytest.fixture
def read_melies_html() -> str:
    """
    Reads the HTML content of the Beethoven page from the test data directory.

    the file is zipped to save space in the repository.

    Returns:
        str: The HTML content of the Beethoven page.
    """
    current_dir = Path(__file__).parent
    zip_path = current_dir / "wikipedia_html/Georges_Melies.html.zip"

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        files = zip_ref.namelist()
        for file in files:
            if file == "Georges_Melies.html":
                print(f"Extracting {file} from the zip file.")
                with zip_ref.open(file) as html_file:
                    return html_file.read().decode("utf-8")


@pytest.fixture(scope="module")
def test_db_settings():
    yield Settings(
        graph_db_uri="bolt://localhost:7687",
    )


@pytest.fixture(scope="function")
def test_person_graphdb(test_db_settings):
    yield PersonGraphHandler(test_db_settings)


@pytest.fixture(scope="function")
def test_film_graphdb(test_db_settings):
    yield FilmGraphHandler(test_db_settings)


@pytest.fixture(scope="function")
def test_memgraph_client(test_db_settings):
    client = GraphDatabase.driver(
        str(test_db_settings.graph_db_uri),
        auth=("", ""),
    )
    yield client
    client.close()


@pytest.fixture(scope="function")
def test_film():
    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )
    film.influences = [
        WOAInfluence(
            parent_uid=film.uid,
            type=WOAType.FILM,
            persons=["Christopher Nolan"],
        ),
    ]
    film.media = FilmMedia(
        **{
            "parent_uid": film.uid,
            "posters": [
                "https://example.com/poster1.jpg",
                "https://example.com/poster2.jpg",
            ],
        }
    )
    film.specifications = FilmSpecifications(
        parent_uid=film.uid,
        title="Inception",
        written_by=["Christopher Nolan"],
    )

    film.actors = [
        FilmActor(
            parent_uid=film.uid,
            full_name="Leonardo DiCaprio",
        ),
        FilmActor(
            parent_uid=film.uid,
            full_name="Joseph Gordon-Levitt",
        ),
    ]
    yield film


@pytest.fixture(scope="function")
def test_person():
    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )

    person.biography = Biography(
        parent_uid=person.uid,
        full_name="Christopher Nolan",
    )

    person.characteristics = PersonCharacteristics(
        parent_uid=person.uid,
        gender=GenderEnum.MALE,
    )

    person.influences = [
        WOAInfluence(
            parent_uid=person.uid,
            persons=["Steven Spielberg"],
        ),
    ]

    yield person
