from typing import List

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--e2e", action="store_true", default=False, help="run e2e tests")


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
