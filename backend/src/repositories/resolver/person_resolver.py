from loguru import logger

from src.entities.content import Section
from src.entities.person import Biography, Person, PersonCharacteristics, PersonMedia
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import IContentExtractor
from src.interfaces.resolver import IEntityResolver
from src.interfaces.similarity import MLProcessor


class BasicPersonResolver(IEntityResolver[Person]):
    """
    in charge of extracting info from the sections and assembling a Film entity.
    """

    entity_extractor: IContentExtractor
    section_searcher: MLProcessor

    def __init__(
        self, entity_extractor: IContentExtractor, section_searcher: MLProcessor
    ):
        self.entity_extractor = entity_extractor
        self.section_searcher = section_searcher

    def resolve(
        self,
        base_info: SourcedContentBase,
        sections: list[Section],
    ) -> Person:
        """
        Assembles a `Person` from the provided html sections.

        TODO:
        - parfois la bio est longue et contient plusieurs <section>, il faudrait découper par partie
        - prendre en compte l'intro d'une page qui ne fait pas partie des sections
        - ex: https://api.wikimedia.org/core/v1/wikipedia/fr/page/Georges_M%C3%A9li%C3%A8s/html

        Args:
            base_info (SourcedContentBase): The base information of the film, including title, permalink, and uid.
            sections (list[Section]): A list of Section objects containing the content to be resolved.

        Returns:
            Person: The assembled Person.
        """

        # retriever title and permalink from the first part
        if not sections or len(sections) == 0:
            raise ValueError("No sections provided to resolve the Film.")

        _entity_to_sections = {
            Biography: ["Biographie"],
            PersonMedia: ["Données clés", "Biographie"],
            PersonCharacteristics: ["Biographie"],
        }

        parts = []

        for entity_type, titles in _entity_to_sections.items():
            for title in titles:

                section: Section = self.section_searcher.process(
                    title=title,
                    sections=sections,
                )

                # there is a corresponding section in the content
                if section is not None:

                    # try to extract the entity from the section content
                    section_entity = self.entity_extractor.extract_entity(
                        content=section.content,
                        entity_type=entity_type,
                    )
                    if section_entity is None:
                        continue

                    logger.debug(
                        f"Found a '{section_entity.__class__.__name__}' in '{section.title}' for content '{base_info.uid}'."
                    )
                    parts.append(section_entity)

        _person = Person(
            uid=base_info.uid,
            title=base_info.title,
            permalink=base_info.permalink,
        )

        for part in parts:
            if isinstance(part, Biography):
                _person.biography = part
            elif isinstance(part, PersonMedia):
                _person.media = part
            elif isinstance(part, PersonCharacteristics):
                _person.characteristics = part

        logger.info(f"Resolved Person: '{_person.title}' : {_person.model_dump()}")

        return _person
