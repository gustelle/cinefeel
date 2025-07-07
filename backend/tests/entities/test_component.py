from src.entities.component import EntityComponent


def test_component_uid_is_deterministic():
    # given
    parent_uid = "parent_123"

    # when
    component_1 = EntityComponent(parent_uid=parent_uid)
    component_2 = EntityComponent(parent_uid=parent_uid)

    # then
    assert parent_uid in component_1.uid
    assert (
        component_1.uid == component_2.uid
    ), "UIDs should be the same for the same parent"


def test_update_uid_not_corresponding():
    # given
    parent_uid = "parent_123"
    another_parent_uid = "parent_456"

    class MyComponent(EntityComponent):
        field: str = "value"

    component_1 = MyComponent(parent_uid=parent_uid, field="value")
    component_2 = MyComponent(parent_uid=another_parent_uid, field="another_value")

    # when
    updated_component = component_1.update(component_2)

    # then
    assert updated_component.uid == component_1.uid, "UID should remain unchanged"
    assert (
        updated_component.field == "value"
    ), "Field should not change when UIDs do not match"


def test_update_list():
    # given
    parent_uid = "parent_123"

    class MyComponent(EntityComponent):
        field: list[str] = []

    component_1 = MyComponent(parent_uid=parent_uid, field=["value1", "value2"])
    component_2 = MyComponent(parent_uid=parent_uid, field=["value2", "value3"])

    # when
    updated_component = component_1.update(component_2)

    # then
    assert updated_component.uid == component_1.uid, "UID should remain unchanged"
    assert all(
        v in updated_component.field
        for v in [
            "value1",
            "value2",
            "value3",
        ]
    ), "Field should be updated with new values from the candidate component"


def test_update_score_lower():
    # given
    parent_uid = "parent_123"

    class MyComponent(EntityComponent):
        field: str = "value"
        score: float = 0.5

    component_1 = MyComponent(parent_uid=parent_uid, field="value", score=0.5)
    component_2 = MyComponent(parent_uid=parent_uid, field="new_value", score=0.3)

    # when
    updated_component = component_1.update(component_2)

    # then
    assert updated_component.uid == component_1.uid, "UID should remain unchanged"
    assert (
        updated_component.field == "value"
    ), "Field should not change when score is lower"
    assert (
        updated_component.score == 0.5
    ), "Score should not change when candidate score is lower"
