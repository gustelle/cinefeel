from pydantic import BaseModel

from src.entities.person import Biography, Person, PersonCharacteristics, PersonMedia
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import IContentExtractor
from src.interfaces.similarity import MLProcessor
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
            Biography: ["Introduction", "Biographie"],
            PersonMedia: ["Données clés", "Biographie"],
            PersonCharacteristics: ["Introduction", "Biographie"],
        }

    def assemble(self, base_info: SourcedContentBase, parts: list[BaseModel]) -> Person:
        """Assemble a Person object from base info and extracted parts."""
        person = Person(
            uid=base_info.uid,
            title=base_info.title,
            permalink=base_info.permalink,
        )
        for part in parts:
            if isinstance(part, Biography):
                person.biography = part
            elif isinstance(part, PersonMedia):
                person.media = part
            elif isinstance(part, PersonCharacteristics):
                person.characteristics = part

        return person
