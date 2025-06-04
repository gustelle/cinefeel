from src.entities.person import Biography, Person, PersonCharacteristics, PersonMedia
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import ExtractionResult, IContentExtractor
from src.interfaces.nlp_processor import MLProcessor
from src.repositories.resolver.abstract_resolver import AbstractResolver


class BasicPersonResolver(AbstractResolver[Person]):
    """
    Responsible for extracting information from sections and assembling a Person entity.

    TODO:
    - prendre en compte les sections enfant
    - prendre en compte les sections sans titre
    - prendre en compte les sections orphanes (sans parent)

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
            Biography: ["Introduction", "Biographie"],
            PersonMedia: ["Données clés", "Biographie"],
            PersonCharacteristics: ["Introduction", "Biographie"],
        }

    def assemble(
        self, base_info: SourcedContentBase, parts: list[ExtractionResult]
    ) -> Person:
        """Assemble a Person object from base info and extracted parts.

        TODO:
        - take into account the score of the extraction results
        - merge parts with the same type
        """
        person = Person(
            uid=base_info.uid,
            title=base_info.title,
            permalink=base_info.permalink,
        )
        for part in parts:
            _ent = part.entity
            if isinstance(_ent, Biography):
                person.biography = _ent
            elif isinstance(_ent, PersonMedia):
                person.media = _ent
            elif isinstance(_ent, PersonCharacteristics):
                person.characteristics = _ent

        return person
