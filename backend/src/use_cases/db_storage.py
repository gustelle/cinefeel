from enum import StrEnum

from prefect import serve

from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.settings import Settings


class StorageType(StrEnum):
    movies = "movies"
    persons = "persons"


class DBStorageUseCase:

    settings: Settings
    _types: list[StorageType]

    def __init__(self, settings: Settings, types: list[StorageType]):
        self.settings = settings
        self._types = types

    def execute(self):

        _flows = []
        if "movies" in self._types:

            _flows.append(
                db_storage_flow.to_deployment(
                    name="movies_storage",
                    description="Stores movies in the database.",
                    parameters={
                        "settings": self.settings,
                        "entity_type": "Movie",
                    },
                )
            )

        if "persons" in self._types:

            _flows.append(
                db_storage_flow.to_deployment(
                    name="persons_storage",
                    description="Stores persons in the database.",
                    parameters={
                        "settings": self.settings,
                        "entity_type": "Person",
                    },
                )
            )

        serve(
            *_flows,
        )
