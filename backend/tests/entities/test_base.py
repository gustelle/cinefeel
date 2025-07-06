import orjson
from pydantic import Field

from src.entities.component import EntityComponent


def test_uid_is_assigned():
    # given
    my_uid = "my-uid-12345"

    # When
    storable = EntityComponent(uid=my_uid, parent_uid="parent-123")

    # Then
    assert storable.uid != my_uid  # UID should be modified by the model_validator


def test_serialize_by_alias_is_default_behavior():

    # given
    uid = "uid-12345"

    class MyStorable(EntityComponent):
        my_field: str = Field(
            ...,
            serialization_alias="coucou",
        )

    my_instance = MyStorable(uid=uid, my_field="Hello World", parent_uid="parent-123")

    # when
    serialized = my_instance.model_dump_json()

    # then
    assert "coucou" in orjson.loads(serialized)


def test_load_model_from_json_with_alias():

    # given

    class MyStorable(EntityComponent):
        my_field: str = Field(
            ...,
            serialization_alias="coucou",
            validation_alias="coucou",
        )

    serialized = '{"uid":"uid-12345","coucou":"Hello World","parent_uid":"parent-123"}'

    # when
    instance = MyStorable.model_validate_json(serialized)

    # then
    assert instance.my_field == "Hello World"
