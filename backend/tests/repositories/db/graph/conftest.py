import time

import docker
import pytest
from docker import DockerClient
from neo4j import GraphDatabase

from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.settings import Settings

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
