import sys
from typing import Literal

from .movie import Movie
from .person import Person


def get_entity_class(entity_type: Literal["Movie", "Person"]):
    try:
        thismodule = sys.modules[__name__]
        return getattr(thismodule, entity_type)
    except AttributeError as e:
        raise ValueError(f"Unsupported entity type: {entity_type}") from e


__all__ = ["Person", "Movie", "get_entity_class"]
