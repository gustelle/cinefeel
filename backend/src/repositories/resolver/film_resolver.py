from pydantic import BaseModel

from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.entities.source import SourcedContentBase
from src.entities.woa import WOAInfluence, WOAType
from src.interfaces.extractor import IContentExtractor
from src.interfaces.nlp_processor import MLProcessor
from src.repositories.resolver.abstract_resolver import AbstractResolver


class BasicFilmResolver(AbstractResolver[Film]):
    """
    Responsible for extracting information from sections and assembling a Person entity.

    """

    def __init__(
        self,
        entity_extractor: IContentExtractor,
        section_searcher: MLProcessor,
        entity_to_sections: dict[type, list[str]] = None,
    ):
        self.entity_extractor = entity_extractor
        self.section_searcher = section_searcher
        self.entity_to_sections = entity_to_sections or {
            FilmMedia: ["Données clés", "Fragments"],
            FilmSpecifications: ["Fiche technique"],
            FilmActor: ["Distribution"],
            FilmSummary: [
                "Synopsis",
                "Résumé",
                "Introduction",
            ],
        }

    def assemble(self, base_info: SourcedContentBase, parts: list[BaseModel]) -> Film:
        """Assemble a Person object from base info and extracted parts."""
        _film = Film(
            uid=base_info.uid,
            title=base_info.title,
            permalink=base_info.permalink,
            woa_type=WOAType.FILM,
        )

        for part in parts:
            if isinstance(part, FilmSummary):
                _film.summary = part
            elif isinstance(part, FilmMedia):
                _film.media = part
            elif isinstance(part, FilmSpecifications):
                _film.specifications = part
            elif isinstance(part, FilmActor):
                if _film.actors is None:
                    _film.actors = []
                _film.actors.append(part)
            elif isinstance(part, WOAInfluence):
                if _film.influences is None:
                    _film.influences = []
                _film.influences.append(part)

        return _film
