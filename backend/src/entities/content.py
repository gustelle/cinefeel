from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class InfoBoxElement(BaseModel):
    title: str
    content: str | None


class Section(BaseModel):
    title: str
    content: str | None
