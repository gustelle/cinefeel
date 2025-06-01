from loguru import logger

from src.entities.content import Section
from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.entities.source import SourcedContentBase
from src.entities.woa import WOAInfluence, WOAType
from src.interfaces.extractor import IContentExtractor
from src.interfaces.resolver import IEntityResolver
from src.interfaces.similarity import MLProcessor


class BasicFilmResolver(IEntityResolver[Film]):
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
    ) -> Film:
        """
        Assembles a `Film` from the provided html sections.

        Args:
            base_info (SourcedContentBase): The base information of the film, including title, permalink, and uid.
            sections (list[Section]): A list of Section objects containing the content to be resolved.

        Returns:
            Film: The assembled Film.
        """

        # retriever title and permalink from the first part
        if not sections or len(sections) == 0:
            raise ValueError("No sections provided to resolve the Film.")

        _entity_to_sections = {
            FilmMedia: ["Données clés", "Fragments"],
            FilmSpecifications: ["Fiche technique"],
            FilmActor: ["Distribution"],
            FilmSummary: ["Synopsis", "Résumé"],
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

        _film = Film(
            uid=base_info.uid,
            title=base_info.title,
            permalink=base_info.permalink,
            woa_type=WOAType.FILM,
        )

        for part in parts:
            if isinstance(part, FilmSummary):
                _film.summary = part
            elif isinstance(part, FilmMedia):
                _film.media = part
            elif isinstance(part, FilmSpecifications):
                _film.specifications = part
            elif isinstance(part, FilmActor):
                if _film.actors is None:
                    _film.actors = []
                _film.actors.append(part)
            elif isinstance(part, WOAInfluence):
                if _film.influences is None:
                    _film.influences = []
                _film.influences.append(part)

        logger.info(f"Resolved Film: '{_film.title}' : {_film.model_dump()}")

        return _film
