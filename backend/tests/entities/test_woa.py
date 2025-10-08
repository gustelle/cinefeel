from src.entities.woa import WOAInfluence


def test_WOAInfluence_has_no_empty_value():
    # GIVEN

    influence = WOAInfluence(
        persons=["", "  ", None, "John Doe"],
        work_of_arts=["", "  ", None, "Mona Lisa"],
        parent_uid="parent-uid-123",
    )

    # THEN
    assert influence.persons == ["John Doe"]
    assert influence.work_of_arts == ["Mona Lisa"]
