def test_get_entity_class():
    from src.entities import get_entity_class
    from src.entities.movie import Movie
    from src.entities.person import Person

    assert get_entity_class("Movie") is Movie
    assert get_entity_class("Person") is Person


def test_get_entity_class_invalid():
    import pytest

    from src.entities import get_entity_class

    with pytest.raises(ValueError) as exc_info:
        get_entity_class("InvalidEntity")

    assert "Unsupported entity type: InvalidEntity" in str(exc_info.value)
