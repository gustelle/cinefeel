from src.entities.person import Person
from src.repositories.orchestration.tasks.task_storage import execute_task
from src.settings import Settings
from tests.repositories.orchestration.stubs.stub_storage import StubStorage


def test_batch_insert_task(test_settings: Settings, test_person: Person):

    # given
    # a runner

    # generate 10 entities
    test_persons = [
        test_person.model_copy(update={"title": f"person_{i}"}) for i in range(1, 10)
    ]

    # input storage with two entities
    input_storage = StubStorage[Person](test_persons)
    output_storage = StubStorage[Person]()

    # when
    execute_task.fn(  # type: ignore
        input_storage=input_storage,
        output_storage=output_storage,
    )

    # then
    assert input_storage.is_scanned, "Input storage was not scanned."
    assert (
        output_storage.is_inserted
    ), "Entities were not inserted into the output storage."
    assert len(output_storage._inserted) == len(
        test_persons
    ), "Not all entities were inserted into the output storage."


def test_batch_insert_task_per_batch(test_settings: Settings, test_person: Person):

    # given
    # a runner

    # generate 10 entities
    test_persons = [
        test_person.model_copy(update={"title": f"person_{i}"}) for i in range(1, 101)
    ]

    # input storage with two entities
    input_storage = StubStorage[Person](test_persons)
    output_storage = StubStorage[Person]()

    # when
    execute_task.fn(  # type: ignore
        input_storage=input_storage,
        output_storage=output_storage,
        batch_size=10,  # smaller batch size for testing
    )

    # then
    assert input_storage.is_scanned, "Input storage was not scanned."
    assert (
        output_storage.is_inserted
    ), "Entities were not inserted into the output storage."
    assert len(output_storage._inserted) == len(
        test_persons
    ), "Not all entities were inserted into the output storage."
