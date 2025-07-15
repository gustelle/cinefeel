import kuzu
from pydantic_settings import BaseSettings

from src.entities.film import Film
from src.entities.person import Person
from src.settings import Settings

from .abstract_graph import AbstractGraphHandler


class FimGraphHandler(AbstractGraphHandler[Film]):

    # required to handle relationships with Person entities
    person_client: AbstractGraphHandler[Person]

    def __init__(
        self,
        client: kuzu.Database | None = None,
        settings: BaseSettings = Settings(),
    ):
        super().__init__(client, settings)
        self.person_client = AbstractGraphHandler[Person](client, settings)
