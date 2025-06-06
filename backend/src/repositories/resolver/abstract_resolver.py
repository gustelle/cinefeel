import abc

from loguru import logger

from src.entities.composable import Composable
from src.entities.content import Section
from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import IContentExtractor
from src.interfaces.nlp_processor import MLProcessor
from src.interfaces.resolver import IEntityResolver


class AbstractResolver[T: Composable](abc.ABC, IEntityResolver[T]):
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
        results = self.extract_entities(sections, base_info)

        # assemble the entity from the base info and extracted parts
        entity = self.assemble(base_info, results)

        logger.info(f"Resolved Entity: '{entity.title}' : {entity.model_dump()}")
        return entity

    def extract_entities(
        self, sections: list[Section], base_info: SourcedContentBase
    ) -> list[ExtractionResult]:
        """Extract entities from sections based on predefined mappings.

        Sections may have children, in this case the children are considered to retrieve entities;

        Args:
            sections (list[Section]): List of Section objects containing content.
            uid (str): Unique identifier for the content being processed.
                just for logging purposes.

        Returns:
            list[ExtractionResult]: List of ExtractionResult objects containing extracted entities and their confidence scores.

        """

        extracted_parts: list[ExtractionResult] = []
        for entity_type, titles in self.entity_to_sections.items():

            logger.debug(
                f"Processing entity type '{entity_type.__name__}' with titles: {titles} for content '{base_info.uid}'."
            )

            section: Section  # for type checking

            for title in titles:

                section = self.section_searcher.process(title=title, sections=sections)
                if section is None:
                    continue

                # take into account the section children
                if section.children:
                    for child in section.children:
                        result = self.entity_extractor.extract_entity(
                            content=child.content,
                            entity_type=entity_type,
                            base_info=base_info,
                        )
                        if result.entity is None:
                            continue
                        logger.debug(
                            f"<{base_info.uid}>-[{section.title}]-[{child.title}] {result.entity.model_dump(mode='json')} (confidence {result.score})."
                        )
                        extracted_parts.append(result)

                result = self.entity_extractor.extract_entity(
                    content=section.content,
                    entity_type=entity_type,
                    base_info=base_info,
                )
                if result.entity is None:
                    continue
                logger.debug(
                    f"<{base_info.uid}>-[{section.title}] {result.entity.model_dump(mode='json')} (confidence {result.score})."
                )
                extracted_parts.append(result)

        return extracted_parts

    def assemble(
        self, base_info: SourcedContentBase, parts: list[ExtractionResult]
    ) -> T:
        """Assemble a film object from base info and extracted parts."""

        return self.entity_type.from_parts(base_info, parts, by_alias=True)
