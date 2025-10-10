from unittest.mock import patch

from src.entities.person import Person
from src.interfaces.http_client import HttpError
from src.repositories.orchestration.tasks.task_relationship import (
    EntityRelationshipTask,
)
from src.settings import Settings
from tests.repositories.orchestration.stubs.stub_http import StubSyncHttpClient
from tests.repositories.orchestration.stubs.stub_storage import StubStorage


def test_task_load_entity_by_name_from_storage(
    test_settings: Settings,
    test_person: Person,
):
    """case where the entity is found in the storage"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"
    permalink = f"https://fr.wikipedia.org/wiki/{page_id}"

    runner = EntityRelationshipTask(
        settings=test_settings,
        http_client=StubSyncHttpClient(
            response={
                "key": page_id,
            }
        ),
    )

    # an input storage with a film entity
    clint = test_person.model_copy(
        update={
            "permalink": permalink,
        }
    )
    storage = StubStorage([clint])

    # when
    result = runner.load_entity_by_name(name=name, input_storage=storage)

    # then
    assert isinstance(result, Person), "should return a Person entity"
    assert result.permalink == permalink


def test_task_load_entity_by_name_not_existing_in_storage(
    test_settings: Settings, test_person: Person
):
    """the person is found in wikipedia, but not in the storage"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"

    runner = EntityRelationshipTask(
        settings=test_settings,
        http_client=StubSyncHttpClient(
            response={
                "key": page_id,
            }
        ),
    )

    storage = StubStorage(None, entity_type=Person)  # nothing in storage

    # when
    with patch(
        "src.repositories.orchestration.tasks.task_relationship.emit_event"
    ) as mock_emit:
        # Appelle la tâche Prefect (directement ou via .run si besoin)
        result = runner.load_entity_by_name(name=name, input_storage=storage)

    # then
    assert result is None
    # verify the event is emitted
    # (we don't check the return value here, as Prefect tasks return a PrefectFuture)
    assert mock_emit.called
    mock_emit.assert_called_with(
        event="extract.entity",
        resource={"prefect.resource.id": page_id},
        payload={"entity_type": "Person"},
    )


def test_task_load_entity_by_name_not_existing_in_wikipedia(
    test_settings: Settings, test_person: Person
):
    """the entity is not found in the storage, we try to load it from wikipedia, but it is not found there either"""
    # given
    # a runner
    page_id = "Clint_Eastwood"
    name = "Clint Eastwood"
    permalink = f"https://fr.wikipedia.org/wiki/{page_id}"

    runner = EntityRelationshipTask(
        settings=test_settings,
        http_client=StubSyncHttpClient(
            raise_exc=HttpError("Not Found", status_code=404)
        ),
    )

    # an input storage with a film entity
    clint = test_person.model_copy(
        update={
            "permalink": permalink,
        }
    )
    storage = StubStorage([clint])

    # when
    # when
    with patch(
        "src.repositories.orchestration.tasks.task_relationship.emit_event"
    ) as mock_emit:
        result = runner.load_entity_by_name(name=name, input_storage=storage)

    # then
    assert result is None, "should return None if the entity is not found in wikipedia"
    assert not mock_emit.called, "should not emit an event if the entity is not found"
