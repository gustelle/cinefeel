from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.interfaces.extractor import IContentExtractor
from src.interfaces.nlp_processor import Processor
from src.repositories.resolver.abstract_resolver import AbstractResolver


class BasicFilmResolver(AbstractResolver[Film]):
    """
    Responsible for extracting information from sections and assembling a Person entity.

    """

    def __init__(
        self,
        entity_extractor: IContentExtractor,
        section_searcher: Processor,
        entity_to_sections: dict[type, list[str]] = None,
    ):
        self.entity_extractor = entity_extractor
        self.section_searcher = section_searcher
        self.entity_to_sections = entity_to_sections or {
            FilmMedia: ["Données clés", "Fragments", ""],
            FilmSpecifications: ["Fiche technique", ""],
            FilmActor: ["Distribution"],
            FilmSummary: ["Synopsis", "Résumé", "Introduction", ""],
        }
