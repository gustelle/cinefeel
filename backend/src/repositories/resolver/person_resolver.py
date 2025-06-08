from src.entities.person import Biography, Person, PersonCharacteristics, PersonMedia
from src.interfaces.extractor import IContentExtractor
from src.interfaces.nlp_processor import MLProcessor
from src.repositories.resolver.abstract_resolver import AbstractResolver


class BasicPersonResolver(AbstractResolver[Person]):
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
            Biography: ["Données clés", "Introduction", "Biographie", ""],
            PersonMedia: ["Données clés", "Biographie", ""],
            PersonCharacteristics: ["Données clés", "Introduction", "Biographie", ""],
        }
