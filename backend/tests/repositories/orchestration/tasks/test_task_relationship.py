from unittest.mock import patch

from src.entities.person import Person
from src.exceptions import HttpError
from src.repositories.orchestration.tasks.task_relationship import connect_by_name
from src.settings import Settings
from tests.repositories.orchestration.stubs.stub_http import StubSyncHttpClient
from tests.repositories.orchestration.stubs.stub_storage import StubStorage


def test_connect_by_name_from_storage(
    test_person: Person,
):
    """case where the entity is found in the storage"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"
    permalink = f"https://fr.wikipedia.org/wiki/{page_id}"

    http_client = StubSyncHttpClient(
        response={
            "key": page_id,
        }
    )

    clint = test_person.model_copy(
        update={
            "permalink": permalink,
        }
    )
    storage = StubStorage([clint])

    # # when
    connect_by_name(
        test_person, name=name, input_storage=storage, http_client=http_client
    )

    # # then
    assert False


def test_connect_by_name_not_existing_in_storage(test_person: Person):
    """the person is found in wikipedia, but not in the storage"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"

    http_client = StubSyncHttpClient(
        response={
            "key": page_id,
        }
    )

    storage = StubStorage(None, entity_type=Person)  # nothing in storage

    # # when
    with patch(
        "src.repositories.orchestration.tasks.task_relationship.emit_event"
    ) as mock_emit, patch(
        "src.repositories.orchestration.tasks.task_relationship.get_page_id",
        return_value=page_id,
    ):
        # Appelle la tâche Prefect (directement ou via .run si besoin)
        connect_by_name(
            test_person, name=name, input_storage=storage, http_client=http_client
        )

    # then
    assert False
    # verify the event is emitted
    # (we don't check the return value here, as Prefect tasks return a PrefectFuture)
    assert mock_emit.called
    mock_emit.assert_called_with(
        event="extract.entity",
        resource={"prefect.resource.id": page_id},
        payload={"entity_type": "Person"},
    )


def test_connect_by_name_not_existing_in_wikipedia(
    test_settings: Settings, test_person: Person
):
    """the entity is not found in the storage, we try to load it from wikipedia, but it is not found there either"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"
    permalink = f"https://fr.wikipedia.org/wiki/{page_id}"

    http_client = StubSyncHttpClient(raise_exc=HttpError("Not Found", status_code=404))

    # # an input storage with a film entity
    clint = test_person.model_copy(
        update={
            "permalink": permalink,
        }
    )
    storage = StubStorage([clint])

    # # when
    connect_by_name(
        test_person, name=name, input_storage=storage, http_client=http_client
    )

    # # then
    assert False, "a loose coupling should be established here"


def test_connect_by_name_wikipedia_scraping_throws_http_error(
    test_settings: Settings, test_person: Person
):
    """the entity is not found in the storage, we try to load it from wikipedia, but it is not found there either"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"
    permalink = f"https://fr.wikipedia.org/wiki/{page_id}"

    http_client = StubSyncHttpClient(raise_exc=HttpError("Not Found", status_code=404))

    # # an input storage with a film entity
    clint = test_person.model_copy(
        update={
            "permalink": permalink,
        }
    )
    storage = StubStorage([clint])

    # # when
    connect_by_name(
        test_person, name=name, input_storage=storage, http_client=http_client
    )

    # # then
    assert False
