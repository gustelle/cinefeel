import abc

from loguru import logger

from src.entities.composable import Composable
from src.entities.content import Section
from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase
from src.interfaces.extractor import IContentExtractor
from src.interfaces.nlp_processor import Processor
from src.interfaces.resolver import IEntityResolver
from src.settings import Settings


class AbstractResolver[T: Composable](abc.ABC, IEntityResolver[T]):
    """
    Abstract class for resolvers.

    Make it generic to allow different types of resolvers to implement their own logic.
    """

    entity_type: T
    entity_to_sections: dict[type, list[str]]
    entity_extractor: IContentExtractor
    section_searcher: Processor
    settings: Settings

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

        # don't process all sections, but only the ones that are relevant
        sections = self.filter_sections(sections)

        # Extract entities from sections
        results = self.extract_entities(sections, base_info)

        # assemble the entity from the base info and extracted parts
        entity = self.assemble(base_info, results)

        entity = self.patch_media(entity, sections)

        logger.info(f"Resolved Entity: '{entity.title}' : {entity.model_dump()}")
        return entity

    def filter_sections(self, sections: list[Section]) -> list[Section]:
        """Filter sections based on predefined criteria.

        - use `sections_max_children` to limit the number of children per section.
        - use `sections_max_per_page` to limit the number of sections per page.

        Args:
            sections (list[Section]): List of Section objects to filter.

        Returns:
            list[Section]: Filtered list of Section objects.
        """

        # choose the longest sections if there are more than `sections_max_per_page`
        if sections and len(sections) > self.settings.sections_max_per_page:
            sections = sorted(
                sections,
                key=lambda section: len(section.content),
                reverse=True,
            )[: self.settings.sections_max_per_page]

        # limit the number of children per section
        # by choosing the longest children
        # recursively
        for section in sections:
            if (
                section.children
                and len(section.children) > self.settings.sections_max_children
            ):
                section.children = sorted(
                    section.children,
                    key=lambda child: len(child.content),
                    reverse=True,
                )[: self.settings.sections_max_children]

        return sections

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

        logger.debug(
            f"Content '{base_info.uid}' being processed with {len(sections)} sections."
        )

        for section in sections:
            if section.children:
                logger.debug(
                    f"  > Section '{section.title}' has {len(section.children)} children."
                )

        extracted_parts: list[ExtractionResult] = []
        for entity_type, titles in self.entity_to_sections.items():

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
                            f"'{section.title}/{child.title}' > found entity: {result.entity.model_dump_json()} ({result.score:.2f})"
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
                    f"'{section.title}' > found entity: {result.entity.model_dump_json()} ({result.score:.2f})"
                )

                extracted_parts.append(result)

        return extracted_parts

    def assemble(
        self, base_info: SourcedContentBase, parts: list[ExtractionResult]
    ) -> T:
        """Assemble a film object from base info and extracted parts."""

        return self.entity_type.from_parts(base_info, parts)

    @abc.abstractmethod
    def patch_media(self, entity: T, sections: list[Section]) -> T:
        """Patch media into the entity from the sections."""
        raise NotImplementedError("This method should be implemented by subclasses.")
