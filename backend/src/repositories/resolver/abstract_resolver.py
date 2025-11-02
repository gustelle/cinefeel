import abc

from loguru import logger

from src.entities.composable import Composable
from src.entities.content import Section
from src.entities.ml import ExtractionResult
from src.interfaces.nlp_processor import Processor
from src.interfaces.resolver import IEntityResolver, ResolutionConfiguration
from src.settings import MLSettings, SectionSettings


class AbstractResolver[T: Composable](abc.ABC, IEntityResolver[T]):
    """
    A resolver assembles a `Composable` entity from provided sections.
    """

    entity_type: T
    configurations: list[ResolutionConfiguration]
    section_searcher: Processor
    section_settings: SectionSettings
    ml_settings: MLSettings

    def __init__(
        self,
        configurations: list[ResolutionConfiguration],
        section_searcher: Processor,
        section_settings: SectionSettings = None,
        ml_settings: MLSettings = None,
    ):

        self.section_searcher = section_searcher
        self.configurations = configurations
        self.section_settings = section_settings or SectionSettings()
        self.ml_settings = ml_settings or MLSettings()

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
        base_info: Composable,
        sections: list[Section],
    ) -> T:
        """
        Assembles a `Composable` from the provided sections.

        Args:
            base_info (Composable): Base information including title, permalink, and uid.
            sections (list[Section]): List of Section objects containing content.

        Returns:
            Composable: The assembled entity.
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

        entity = self.validate_entity(entity)

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
        if sections and len(sections) > self.section_settings.max_per_page:
            sections = sorted(
                sections,
                key=lambda section: len(section.content),
                reverse=True,
            )[: self.section_settings.max_per_page]

        # limit the number of children per section
        # by choosing the longest children
        # recursively
        for section in sections:
            if (
                section.children
                and len(section.children) > self.section_settings.max_children
            ):
                section.children = sorted(
                    section.children,
                    key=lambda child: len(child.content),
                    reverse=True,
                )[: self.section_settings.max_children]

        return sections

    def extract_entities(
        self, sections: list[Section], base_info: Composable
    ) -> list[ExtractionResult]:
        """
        Searches for entities in the provided sections and extracts them,
        according to the configurations defined in the resolver:
        - 1st, it searches for sections with titles matching the configuration.
        - 2nd, it extracts entities from the content of those sections.

        Args:
            sections (list[Section]): List of Section objects containing content.
            uid (str): Unique identifier for the content being processed.
                just for logging purposes.

        Returns:
            list[ExtractionResult]: List of ExtractionResult objects containing extracted entities and their confidence scores.

        """

        extracted_parts: list[ExtractionResult] = []
        for config in self.configurations:

            section: Section  # for type checking

            for title in config.section_titles:

                section = self.section_searcher.process(title=title, sections=sections)

                if section is None:
                    logger.trace(f"No section found for title: '{title}'")
                    continue

                try:

                    # process main section removing children
                    # because we already processed them
                    result = config.extractor.extract_entity(
                        content=section.content,
                        media=section.media,
                        entity_type=config.extracted_type,
                        parent=base_info,
                    )

                    logger.trace(
                        f"Extracted entity from section '{section.title}' : {result.model_dump_json(indent=2)}"
                    )

                    if result.entity is None:
                        continue

                    result.resolve_as = config.resolve_as

                    extracted_parts.append(result)

                    # process children
                    if section.children:
                        for child in section.children:

                            result = config.extractor.extract_entity(
                                content=child.content,
                                media=child.media,
                                entity_type=config.extracted_type,
                                parent=base_info,
                            )

                            if result.entity is None:
                                continue

                            result.resolve_as = config.resolve_as

                            extracted_parts.append(result)

                except Exception as e:
                    # log the error and continue
                    import traceback

                    logger.error(traceback.format_exc())
                    logger.error(f"Error extracting entity from section: {e}")
                    continue

        return extracted_parts

    def assemble(self, base_info: Composable, parts: list[ExtractionResult]) -> T:
        """Assemble a film object from base info and extracted parts."""

        return self.entity_type.compose(
            title=base_info.title,
            permalink=base_info.permalink,
            uid=base_info.uid,
            parts=parts,
        )

    @abc.abstractmethod
    def patch_media(self, entity: T, sections: list[Section]) -> T:
        """Patch media into the entity from the sections,
        because media extraction is not reliable enough to be done during extraction.

        it should directly be taken from the sections and patched into the entity.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abc.abstractmethod
    def validate_entity(self, entity: T) -> T:
        """Entity-specific validation logic

        for instance we can find here checks on mandatory fields,
        normalization of certain fields, etc.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
