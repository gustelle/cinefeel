import time

import docker
import pytest
from docker import DockerClient

# see https://stackoverflow.com/questions/46733332/how-to-monkeypatch-the-environment-using-pytest-in-conftest-py
mp = pytest.MonkeyPatch()

mp.setenv("REDIS_STORAGE_DSN", "redis://localhost:6378")


DOCKER_REDIS_IMAGE_NAME = "redis:8"
DOCKER_REDIS_CONTAINER_NAME = "redis_test_storage"


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
            ports={"6379": "6378"},
        )

        wait_for_redis = True
        print("--- Launching Redis ---")
        while wait_for_redis:
            logs = container.logs()
            time.sleep(0.5)
            elapsed = time.time() - start_time
            print(str(logs))
            if "Ready to accept connections tcp" in str(logs):
                wait_for_redis = False
                print(f"\r\nLaunched Redis in {round(elapsed, 2)} seconds")
                print("--- Redis started ---")

    else:
        print("--- Running tests in standalone mode ---")

    yield

    if not standalone:
        remove_redis(docker_client)
