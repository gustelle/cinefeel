import kuzu
from pydantic_settings import BaseSettings

from src.entities.film import Film
from src.entities.person import Person
from src.settings import Settings

from .abstract_graph import AbstractGraphHandler


class PersonGraphHandler(AbstractGraphHandler[Person]):

    # required to handle relationships with Film entities
    film_client: AbstractGraphHandler[Film]

    def __init__(
        self,
        client: kuzu.Database | None = None,
        settings: BaseSettings = Settings(),
    ):
        super().__init__(client, settings)
        self.film_client = AbstractGraphHandler[Film](client, settings)
