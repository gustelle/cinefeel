from src.entities.person import Person

from .abstract_graph import AbstractGraphHandler
from .film_graph import FimGraphHandler


class PersonGraphHandler(AbstractGraphHandler[Person]):

    film_client: FimGraphHandler
