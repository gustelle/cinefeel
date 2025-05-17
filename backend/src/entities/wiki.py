from pydantic import BaseModel, ConfigDict, Field


class WikiPageLink(BaseModel):
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
