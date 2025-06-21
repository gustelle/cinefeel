
from src.entities.content import Section
from src.entities.nationality import NATIONALITIES
from src.entities.person import Biography, Person, PersonCharacteristics, PersonMedia
from src.interfaces.extractor import IDataMiner
from src.interfaces.nlp_processor import Processor
from src.repositories.html_parser.wikipedia_info_retriever import (
    INFOBOX_SECTION_TITLE,
    ORPHAN_SECTION_TITLE,
)
from src.repositories.ml.phonetics import PhoneticSearch
from src.repositories.resolver.abstract_resolver import AbstractResolver
from src.settings import Settings


class BasicPersonResolver(AbstractResolver[Person]):
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
            Biography: [INFOBOX_SECTION_TITLE, ORPHAN_SECTION_TITLE, "Biographie", ""],
            PersonMedia: [INFOBOX_SECTION_TITLE, "Biographie", ""],
            PersonCharacteristics: [
                INFOBOX_SECTION_TITLE,
                ORPHAN_SECTION_TITLE,
                "Biographie",
                "",
            ],
        }

        self.settings = Settings()

    def patch_media(self, entity: Person, sections: list[Section]) -> Person:
        """
        Patches the media of the Person entity with the media extracted from sections.

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
                uid=f"media_{entity.uid}",
                photos=posters,
                other_medias=audios + videos,
            )

        return entity

    def validate_entity(self, entity: Person) -> Person:

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

        # parse date_naissance
        # ddp = DateDataParser(languages=["fr"])
        # birth_date = entity.biography.birth_date

        # logger.debug(
        #     f"Validating entity '{entity.title}' with birth date '{birth_date}' and nationalities {valid_nationalities}."
        # )

        # if birth_date:
        #     parsed_date = ddp.get_date_data(birth_date)
        #     logger.debug(
        #         f"Parsed birth date '{birth_date}' for person '{entity.title}': {parsed_date}"
        #     )
        #     if parsed_date and parsed_date["date_obj"]:
        #         birth_date = parsed_date["date_obj"].isoformat()
        #     else:
        #         logger.warning(
        #             f"Could not parse birth date '{birth_date}' for person '{entity.title}'."
        #         )
        #         birth_date = None

        return entity.model_copy(
            update={
                "biography": entity.biography.model_copy(
                    update={
                        "nationalities": valid_nationalities,
                        # "birth_date": birth_date,
                    }
                )
            }
        )
