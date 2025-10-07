from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
)

from .movie import Movie
from .person import Person

SectionTitle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=0,
    ),
]  # may be empty for some sections


class UsualSectionTitles_FR_fr(StrEnum):
    """
    Common section titles found in Wikipedia articles.
    """

    INTRODUCTION = "Introduction"
    INFOBOX = "Données clés"
    TECHNICAL_SHEET = "Fiche technique"
    BIOGRAPHY = "Biographie"
    INFLUENCES = "Influences"
    ANALYSIS = "Analyse"
    CONTEXT = "Contexte"
    SYNOPSIS = "Synopsis"
    SUMMARY = "Résumé"
    DISTRIBUTION = "Distribution"
    NO_TITLE = ""  # sections that don't have a title


class PageLink(BaseModel):
    """
    a link to a page on Wikipedia.
    """

    # use python-re to support lookbehind assertions
    # see https://github.com/pydantic/pydantic/issues/9729
    model_config = ConfigDict(regex_engine="python-re")

    page_title: str | None = Field(
        None,
        description="The title of the link. May not be present in all cases.",
        examples=[
            "À Biribi, disciplinaires français",
        ],
    )
    page_id: str = Field(
        ...,
        description="The ID of the linked page on Wikipedia. Must not start with a slash or './'.",
        pattern=r"^(?!\.?\/).*",
        examples=["À_Biribi,_disciplinaires_français"],
    )

    entity_type: Literal[Movie.__name__, Person.__name__] = Field(
        ...,
        description="The type of content the link refers to. This can be either 'Movie' or 'Person'.",
        examples=["Movie", "Person"],
    )


class TableOfContents(PageLink):
    """Configuration for a Wikipedia Table-of-content (TOC) page.

    A table of content page is a page that contains a list of links to other pages.
    For example, the page "Liste de films français sortis en 1907" contains a list of links to
    all the films released in 1907.
    """

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    inner_links_selector: str | None = Field(
        None,
        description="""
            The CSS selector to use to extract the (list of) links from the table of contents.
            The selector should return a list of links to the pages to download.
        """,
        examples=[".wikitable td:nth-child(1)"],
        alias="link_selector",
    )


class Section(BaseModel):
    """A wikipedia section, which may contain subsections and media

    A section is identified by a <section> tag in the HTML, and contains optional child sections.
    """

    title: SectionTitle = Field(
        ...,
        description="The title of the section. This is a required field.",
        examples=["Introduction", "Biographie"],
    )
    content: str | None

    children: list[Section] | None = Field(
        default_factory=list,
        description="A list of child sections, if any. This allows for nested sections.",
        repr=False,
    )

    media: list[Media | None] | None = Field(
        default_factory=list,
        description="A list of media associated with the section, if any.",
        repr=False,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return v.strip()


class Media(BaseModel):
    """
    A media is either an image, a video or an audio file
    """

    uid: str = Field(
        ...,
        description="the id of the media",
        examples=["wikipedia:media:film_1234"],
    )

    src: HttpUrl | None = Field(
        None,
        description="The URL of the media",
        examples=["https://example.com/image.jpg"],
    )
    media_type: Literal["image", "video", "audio"] = Field(
        ...,
        description="The type of media, either 'image', 'audio' or 'video'.",
        examples=["image", "video"],
    )
    caption: str | None = Field(
        None,
        description="A caption for the media, if available.",
        examples=["A still from the film", "A portrait of the person"],
    )
