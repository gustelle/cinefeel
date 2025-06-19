from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.interfaces.extractor import IContentExtractor
from src.interfaces.nlp_processor import Processor
from src.repositories.html_parser.wikipedia_info_retriever import (
    INFOBOX_SECTION_TITLE,
    ORPHAN_SECTION_TITLE,
)
from src.repositories.resolver.abstract_resolver import AbstractResolver
from src.settings import Settings


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
            FilmMedia: [INFOBOX_SECTION_TITLE, "Fragments", ""],
            FilmSpecifications: ["Fiche technique", ORPHAN_SECTION_TITLE],
            FilmActor: ["Distribution"],
            FilmSummary: ["Synopsis", "Résumé", ORPHAN_SECTION_TITLE, ""],
        }
        self.settings = Settings()
