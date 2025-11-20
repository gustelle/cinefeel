import tempfile
import time
import zipfile
from pathlib import Path

import docker
import pytest
from docker import DockerClient
from neo4j import GraphDatabase

from src.entities.movie import FilmActor, FilmMedia, FilmSpecifications, Movie
from src.entities.person import Biography, Person
from src.entities.woa import WOAInfluence, WOAType
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
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

# see https://stackoverflow.com/questions/46733332/how-to-monkeypatch-the-environment-using-pytest-in-conftest-py
mp = pytest.MonkeyPatch()

GRAPHDB_NATIVE_PORT = 7687
GRAPHDB_HOST_PORT = 7688
GRAPHDB_URI = f"bolt://localhost:{GRAPHDB_HOST_PORT}"

mp.setenv("GRAPH_DB_URI", GRAPHDB_URI)

DOCKER_MEMGRAPH_IMAGE_NAME = "memgraph/memgraph-mage"
DOCKER_MEMGRAPH_CONTAINER_NAME = "memgraph_test_storage"

REDIS_NATIVE_PORT = 6379
REDIS_HOST_PORT = 6378
mp.setenv("REDIS_STORAGE_DSN", f"redis://localhost:{REDIS_HOST_PORT}")

DOCKER_REDIS_IMAGE_NAME = "redis:8"  # "docker.dragonflydb.io/dragonflydb/dragonfly"
DOCKER_REDIS_CONTAINER_NAME = "redis_test_storage"


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


@pytest.fixture
def read_not_enough_cols_infobox() -> str:
    """
    case where the infobox list cannot be parsed correctly
    """
    return """
    <div class="infobox_v3 infobox infobox--frwiki noarchive large">
        <table>
            <tr class="">
                <td>Something</td>
            </tr>
        </table>
    </div>
    """


@pytest.fixture
def read_defective_table_infobox() -> str:
    """
    case where the infobox table is malformed and cannot be parsed correctly
    """
    return """
    <div class="infobox_v3 infobox infobox--frwiki noarchive large">
        <table>
        </table>
    </div>
    """


@pytest.fixture(scope="function")
def test_film():
    film = Movie(
        title="Inception",
        permalink="https://example.com/inception",
    )
    film.influences = [
        WOAInfluence(
            parent_uid=film.uid,
            type=WOAType.MOVIE,
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

    person.influences = [
        WOAInfluence(
            parent_uid=person.uid,
            persons=["Steven Spielberg"],
        ),
    ]

    yield person


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
                GRAPHDB_NATIVE_PORT: GRAPHDB_HOST_PORT,
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


@pytest.fixture(scope="session")
def test_settings(launch_memgraph):  #

    path = Path(__file__).parent / "start-pages-test.yml"

    # create a temporary directory for local storage
    # which does not depend on the infrastructure of the machine running the tests
    # because on github actions, we don't have control over the file system
    with tempfile.TemporaryDirectory() as tmpdir:

        settings = AppSettings(
            _env_file=None,
            storage_settings=StorageSettings(
                _env_file=None,
                local_directory=(Path(tmpdir) / "data").as_posix(),
                graphdb_uri=GRAPHDB_URI,
                redis_dsn=f"redis://localhost:{REDIS_HOST_PORT}/0",
            ),
            scraping_settings=ScrapingSettings(
                _env_file=None,
                config_file=path.as_posix(),
            ),
            ml_settings=MLSettings(
                _env_file=None,
                similarity_min_score=0.7,
                summary_max_length=512,
                transformer_model_backend="torch",  # ok on local machine with cuda or mps
            ),
            stats_settings=StatsSettings(
                _env_file=None,
                redis_dsn=f"redis://localhost:{REDIS_HOST_PORT}/1",
            ),
            search_settings=SearchSettings(_env_file=None),
            prefect_settings=PrefectSettings(_env_file=None),
            section_settings=SectionSettings(_env_file=None),
        )

        yield settings


@pytest.fixture(scope="function")
def test_person_graphdb(test_settings: AppSettings):
    yield PersonGraphRepository(test_settings.storage_settings)


@pytest.fixture(scope="function")
def test_film_graphdb(test_settings: AppSettings):
    yield MovieGraphRepository(test_settings.storage_settings)


@pytest.fixture(scope="function")
def test_memgraph_client(test_settings: AppSettings):
    client = GraphDatabase.driver(
        str(test_settings.storage_settings.graphdb_uri),
        auth=("", ""),
    )
    yield client
    client.close()


def remove_redis(docker_client: DockerClient):
    try:
        ctn = docker_client.containers.get(DOCKER_REDIS_CONTAINER_NAME)
        ctn.remove(force=True)
    except docker.errors.NotFound:
        pass


@pytest.fixture(scope="session", autouse=True)
def launch_redis(request):
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

        remove_redis(docker_client)

        container = docker_client.containers.run(
            DOCKER_REDIS_IMAGE_NAME,
            detach=True,
            name=DOCKER_REDIS_CONTAINER_NAME,
            ports={REDIS_NATIVE_PORT: REDIS_HOST_PORT},
            # when working with dragonflydb:
            # ulimits=[
            #     docker.types.Ulimit(name="memlock", hard=-1, soft=-1),
            # ],  # disable memory lock
        )

        wait_for_redis = True
        print("--- Launching Redis ---")
        while wait_for_redis:
            logs = container.logs()
            time.sleep(0.5)
            elapsed = time.time() - start_time
            print(str(logs))
            if "Ready to accept connections" in str(logs):
                # if f"listening on 0.0.0.0:{REDIS_NATIVE_PORT}" in str(logs):
                wait_for_redis = False
                print(f"\r\nLaunched Redis in {round(elapsed, 2)} seconds")
                print("--- Redis started ---")

    else:
        print("--- Running tests in standalone mode ---")

    yield

    if not standalone:
        remove_redis(docker_client)
