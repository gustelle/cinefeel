
from pydantic import BaseModel, ConfigDict, Field

# class WikiPageLinkType(StrEnum):
#     """
#     Enum for the type of page.
#     """

#     PERSON = "person"
#     PAGE_LIST = "page_list"
#     WORK_OF_ART = "work_of_art"


class WikiPageLink(BaseModel):
    """
    A class representing a link to a film page on Wikipedia.
    """

    # use python-re to support lookbehind assertions
    # see https://github.com/pydantic/pydantic/issues/9729
    model_config = ConfigDict(regex_engine="python-re")

    # link_type: WikiPageLinkType = Field(
    #     ...,
    #     description="The type of the page linked to. This can be a person, a list of elements, or a work of art.",
    #     examples=["person", "page_list", "work_of_art"],
    # )

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

    def __repr__(self) -> str:
        """human readable representation of the object
        when using print()
        """
        return f"<'{self.page_title}': {self.page_id}>"
