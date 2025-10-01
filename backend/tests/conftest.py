import os
from typing import List

import pytest


def pytest_generate_tests(metafunc):
    """avoid warning :
    The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks
    """
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--e2e", action="store_true", default=False, help="run e2e tests")
    parser.addoption(
        "--standalone",
        default="false",
        help=("pass --standalone to start tests without launching docker containers"),
    )


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: List[pytest.Item]
):
    if config.getoption("--e2e"):
        skip_e2e = pytest.mark.skip(reason="need --e2e option to run")
        for item in items:
            if "e2e" not in item.keywords:
                item.add_marker(skip_e2e)
    else:
        skip_e2e = pytest.mark.skip(reason="use --e2e option to run e2e tests")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
