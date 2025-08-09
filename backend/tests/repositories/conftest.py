import time
import zipfile
from pathlib import Path

import docker
import pytest
from docker import DockerClient
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


# see https://stackoverflow.com/questions/46733332/how-to-monkeypatch-the-environment-using-pytest-in-conftest-py
mp = pytest.MonkeyPatch()

GRAPH_DB_PORT = 7688
GRAPH_DB_URI = f"bolt://localhost:{GRAPH_DB_PORT}"

mp.setenv("GRAPH_DB_URI", GRAPH_DB_URI)


DOCKER_MEMGRAPH_IMAGE_NAME = "memgraph/memgraph-mage:latest"
DOCKER_MEMGRAPH_CONTAINER_NAME = "memgraph_test_storage"


def remove_memgraph(docker_client: DockerClient):
    try:
        ctn = docker_client.containers.get(DOCKER_MEMGRAPH_CONTAINER_NAME)
        ctn.remove(force=True)
    except docker.errors.NotFound:
        pass


@pytest.fixture(scope="session", autouse=True)
def launch_memgraph(request):
    """launch a docker container with mysql before testing"""

    standalone = request.config.getoption("--standalone") == "true"

    if not standalone:
        start_time = time.time()
        docker_client = docker.from_env()
        docker_client.containers.prune()
        docker_client.images.prune()
        docker_client.networks.prune()
        docker_client.volumes.prune()

        print("--- Ran Docker Prune all ---")

        remove_memgraph(docker_client)

        container = docker_client.containers.run(
            DOCKER_MEMGRAPH_IMAGE_NAME,
            detach=True,
            name=DOCKER_MEMGRAPH_CONTAINER_NAME,
            ports={
                7687: GRAPH_DB_PORT,  # Bolt port
                7444: 7444,
            },
        )

        wait_for_memgraph = True
        print("--- Launching Memgraph ---")
        while wait_for_memgraph:
            logs = container.logs()
            time.sleep(0.5)
            elapsed = time.time() - start_time
            print(str(logs))
            if "You are running Memgraph" in str(logs):
                wait_for_memgraph = False
                print(f"\r\nLaunched Memgraph in {round(elapsed, 2)} seconds")
                print("--- Memgraph started ---")

    else:
        print("--- Running tests in standalone mode ---")

    yield

    if not standalone:
        remove_memgraph(docker_client)


@pytest.fixture(scope="module")
def test_db_settings(launch_memgraph):  #

    # we call launch_memgraph fixture to ensure the Memgraph container is running
    # before we create the settings object

    import time

    time.sleep(2)  # wait a bit to ensure the container is ready

    yield Settings(
        graph_db_uri=GRAPH_DB_URI,
    )


@pytest.fixture(scope="function")
def test_person_graphdb(test_db_settings):
    yield PersonGraphHandler(test_db_settings)


@pytest.fixture(scope="function")
def test_film_graphdb(test_db_settings):
    yield FilmGraphHandler(test_db_settings)


@pytest.fixture(scope="function")
def test_memgraph_client(test_db_settings: Settings):
    client = GraphDatabase.driver(
        str(test_db_settings.graph_db_uri),
        auth=("", ""),
    )
    yield client
    client.close()
