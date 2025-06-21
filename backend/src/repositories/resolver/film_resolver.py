from src.entities.content import Section
from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.interfaces.extractor import IDataMiner
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
        entity_extractor: IDataMiner,
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

    def patch_media(self, entity: Film, sections: list[Section]) -> Film:
        """
        Patches the media of the Film entity with the media extracted from sections.

        Args:
            entity (Film): The Film entity to patch.
            sections (list[Section]): List of Section objects containing content.

        Returns:
            Film: The patched Film entity with media.
        """
        # Extract media from sections
        # for the time being, we only extract FilmMedia entities
        # gather all media images and videos
        if not sections:
            return entity

        posters = [
            m.src
            for section in sections
            for m in section.media
            if m.media_type == "image"
        ]
        videos = [
            m.src
            for section in sections
            for m in section.media
            if m.media_type == "video"
        ]
        audios = [
            m.src
            for section in sections
            for m in section.media
            if m.media_type == "audio"
        ]

        # Patch the media into the Film entity
        if posters or videos or audios:
            entity.media = FilmMedia(
                uid=f"media_{entity.uid}",
                posters=posters,
                trailers=videos,
                other_medias=audios,
            )

        return entity

    def validate_entity(self, entity: Film) -> Film:

        return entity
