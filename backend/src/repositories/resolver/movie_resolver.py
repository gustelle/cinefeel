import datetime
import re

from loguru import logger

from src.entities.content import Section
from src.entities.movie import FilmMedia, Movie
from src.repositories.resolver.abstract_resolver import AbstractResolver


class MovieResolver(AbstractResolver[Movie]):

    def patch_media(self, entity: Movie, sections: list[Section]) -> Movie:
        """
        Adds media (posters, trailers, etc.) to the Movie entity based on the media found in the sections.

        Args:
            entity (Movie): The Movie entity to patch.
            sections (list[Section]): List of Section objects containing content.

        Returns:
            Movie: The patched Movie entity with media.
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

        # Patch the media into the Movie entity
        if posters or videos or audios:
            entity.media = FilmMedia(
                posters=posters,
                trailers=videos,
                other_medias=audios,
                parent_uid=entity.uid,
            )

        return entity

    def validate_entity(self, entity: Movie) -> Movie:
        """
        TODO:
        - handle i18n of duration formats
        """

        # validate the duration format
        duration = None
        if entity.specifications and entity.specifications.duration:
            try:
                bool(
                    datetime.datetime.strptime(
                        entity.specifications.duration, "%H:%M:%S"
                    )
                )
                duration = entity.specifications.duration
            except ValueError:

                if m := re.match(
                    r"((?P<H>\d+)\s+heures?\s+)?((?P<M>\d+)\s+minutes?\s+)((?P<S>\d+)\s+secondes?)?",
                    entity.specifications.duration,
                    re.I,
                ):
                    hours = int(m.group("H")) if m.group("H") else 0
                    minutes = int(m.group("M")) if m.group("M") else 0
                    seconds = int(m.group("S")) if m.group("S") else 0
                    duration = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    logger.warning(
                        f"Could not parse duration '{entity.specifications.duration}' for film '{entity.title}', setting to None"
                    )

            return entity.model_copy(
                update={
                    "specifications": entity.specifications.model_copy(
                        update={
                            "duration": duration,
                        }
                    )
                }
            )

        return entity
