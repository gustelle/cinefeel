from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class PageLink(BaseModel):
    """
    A class representing a link to a film page on Wikipedia.
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
        repr=False,
    )
    page_id: str = Field(
        ...,
        description="The ID of the linked page on Wikipedia. Must not start with a slash or './'.",
        pattern=r"^(?!\.?\/).*",
        examples=["À_Biribi,_disciplinaires_français"],
    )

    content_type: Literal["film", "person"] = Field(
        ...,
        description="The type of content the link refers to. This can be either 'film' or 'person'.",
        examples=["film", "person"],
        repr=False,
    )


class Section(BaseModel):
    title: str = Field(
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
    Represents media associated with a film or person.
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
