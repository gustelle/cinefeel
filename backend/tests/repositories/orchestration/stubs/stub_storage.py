from typing import Generator

from src.entities.composable import Composable
from src.entities.relationship import BaseRelationship
from src.interfaces.storage import IRelationshipHandler, IStorageHandler


class StubStorage[T: Composable](IStorageHandler[T]):
    """
    handles storage and retrieval of HTML files on disk.
    """

    entity_type = T

    is_inserted: bool = False
    is_scanned: bool = False
    is_found: bool = False
    _contents_in_store: list[T] = []
    _inserted: list[T] = []

    def __init__(self, input: list[T] = None, entity_type: type[T] = None) -> None:
        self.is_inserted = False
        self.is_scanned = False
        self.is_found = False
        self._contents_in_store = input or []
        self._inserted = []
        self.entity_type = entity_type

    def insert(
        self,
        content_id: str,
        content: T,
        *args,
    ) -> None:
        """Saves the given data to a file."""
        self._inserted.append(content)
        self.is_inserted = True

    def insert_many(
        self,
        contents: list[T],
    ) -> None:
        """Saves multiple contents to persistent storage."""
        print("StubStorage.insert_many called")

        self._inserted.extend(contents)
        self.is_inserted = True

    def scan(
        self,
        *args,
    ) -> Generator[tuple[str, T], None, None]:
        for i, content in enumerate(self._contents_in_store):
            yield i, content
        self.is_scanned = True

    def select(self, content_id, *args, **kwargs):
        raise NotImplementedError

    def query(self, *args, **kwargs) -> list[T]:
        if self._contents_in_store:
            self.is_found = True
            return self._contents_in_store
        return None

    def update(self, content: T, *args, **kwargs) -> T:
        raise NotImplementedError


class StubRelationHandler[T: Composable](StubStorage[T], IRelationshipHandler[T]):

    is_added_relationship: bool = False
    relationship: BaseRelationship

    def add_relationship(
        self,
        relationship,
        *args,
        **kwargs,
    ) -> None:
        self.relationship = relationship
        self.is_added_relationship = True
