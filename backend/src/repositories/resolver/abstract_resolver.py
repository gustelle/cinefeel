import abc

from loguru import logger

from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import IContentExtractor
from src.interfaces.resolver import IEntityResolver
from src.interfaces.similarity import MLProcessor


class AbstractResolver[T: SourcedContentBase](abc.ABC, IEntityResolver[T]):
    """
    Abstract class for resolvers.

    Make it generic to allow different types of resolvers to implement their own logic.
    """

    entity_type: T
    entity_to_sections: dict[type, list[str]]
    entity_extractor: IContentExtractor
    section_searcher: MLProcessor

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type
        return new_cls

    def resolve(
        self,
        base_info: SourcedContentBase,
        sections: list[Section],
    ) -> T:
        """
        Assembles a `SourcedContentBase` from the provided sections.

        Args:
            base_info (SourcedContentBase): Base information including title, permalink, and uid.
            sections (list[Section]): List of Section objects containing content.

        Returns:
            SourcedContentBase: The assembled entity.
        """
        if not sections:
            raise ValueError("No sections provided to resolve the Person.")

        # Extract entities from sections
        extracted_parts = self._extract_entities_from_sections(sections, base_info.uid)

        # Assemble the Person object
        entity = self.assemble(base_info, extracted_parts)

        logger.info(f"Resolved Entity: '{entity.title}' : {entity.model_dump()}")
        return entity

    def _extract_entities_from_sections(
        self, sections: list[Section], uid: str
    ) -> list:
        """Extract entities from sections based on predefined mappings."""
        extracted_parts = []
        for entity_type, titles in self.entity_to_sections.items():
            for title in titles:
                section = self.section_searcher.process(title=title, sections=sections)
                if section is None:
                    continue

                section: Section
                entity = self.entity_extractor.extract_entity(
                    content=section.content, entity_type=entity_type
                )
                if entity is not None:
                    logger.debug(
                        f"Found '{entity.__class__.__name__}' in section '{section.title}' for content '{uid}'."
                    )
                    extracted_parts.append(entity)
        return extracted_parts

    def assemble(self, base_info: SourcedContentBase, parts: list) -> T:
        """Assemble a Person object from base info and extracted parts."""
        raise NotImplementedError(
            "The 'assemble' method must be implemented in subclasses."
        )
