from dateparser.date import DateDataParser
from loguru import logger

from src.entities.content import Section
from src.entities.nationality import NATIONALITIES
from src.entities.person import Biography, Person, PersonMedia
from src.interfaces.nlp_processor import Processor
from src.interfaces.resolver import ResolutionConfiguration
from src.repositories.ml.ollama_date_parser import OllamaDateFormatter
from src.repositories.ml.phonetics import PhoneticSearch
from src.repositories.resolver.abstract_resolver import AbstractResolver
from src.settings import Settings


class PersonResolver(AbstractResolver[Person]):

    def __init__(
        self,
        configurations: list[ResolutionConfiguration],
        section_searcher: Processor,
        settings: Settings = None,
    ):
        self.section_searcher = section_searcher
        self.configurations = configurations
        self.settings = settings or Settings()

    def patch_media(self, entity: Person, sections: list[Section]) -> Person:
        """
        Adds media (images, videos, etc.) to the Person entity based on the media found in the sections.

        Args:
            entity (Person): The Person entity to patch.
            sections (list[Section]): List of Section objects containing content.

        Returns:
            Person: The patched Person entity with media.
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
            entity.media = PersonMedia(
                photos=posters,
                other_medias=audios + videos,
                parent_uid=entity.uid,
            )

        return entity

    def validate_entity(self, entity: Person) -> Person:
        """
        TODO:
        - handle i18n of date formats and nationalities throught a configurable mechanism
        """

        # validate the nationality
        phonetic_search = PhoneticSearch(
            settings=self.settings, corpus=NATIONALITIES["FR"]
        )

        valid_nationalities = []
        if entity.biography and entity.biography.nationalities:
            valid_nationalities = list(
                # make sure to have unique nationalities
                # sometimes the same nationality is mentioned multiple times
                set(
                    [phonetic_search.process(n) for n in entity.biography.nationalities]
                )
            )

        birth_date = entity.biography.birth_date if entity.biography else None
        if birth_date:
            # parse date_naissance
            ddp = DateDataParser(languages=["fr"])
            birth_date = entity.biography.birth_date
            parsed_date = ddp.get_date_data(birth_date)

            if (
                parsed_date
                and parsed_date["date_obj"]
                and parsed_date["date_obj"] is not None
            ):
                birth_date = parsed_date["date_obj"].isoformat()
            else:
                logger.warning(
                    f"Could not parse birth date '{birth_date}' for person '{entity.title}', trying with Ollama"
                )
                chat = OllamaDateFormatter(settings=self.settings)
                birth_date = chat.format(birth_date)

        death_date = entity.biography.death_date if entity.biography else None
        if death_date:
            # parse date_deces
            ddp = DateDataParser(languages=["fr"])
            parsed_date = ddp.get_date_data(death_date)

            if (
                parsed_date
                and parsed_date["date_obj"]
                and parsed_date["date_obj"] is not None
            ):
                death_date = parsed_date["date_obj"].isoformat()
            else:
                logger.warning(
                    f"Could not parse death date '{death_date}' for person '{entity.title}', trying with Ollama."
                )
                chat = OllamaDateFormatter(settings=self.settings)
                death_date = chat.format(death_date)

        if not entity.biography:

            entity.biography = Biography(
                full_name=entity.title,
                parent_uid=entity.uid,
            )

            return entity

        return entity.model_copy(
            update={
                "biography": entity.biography.model_copy(
                    update={
                        "nationalities": valid_nationalities,
                        "birth_date": birth_date,
                        "death_date": death_date,
                    }
                )
            }
        )
