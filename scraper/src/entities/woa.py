from pydantic import BaseModel, Field


class WorkOfArt(BaseModel):
    """
    Represents a work of art with a name and an optional list of roles.
    """

    uid: str | None = Field(
        None,
        description="The unique ID of the work of art. This is used to identify the work of art in the database.",
    )
    title: str
    type: str | None = Field(
        None,
        description="The type of the work of art. ",
        examples=["painting", "sculpture", "drawing", "photography"],
    )
    work_of_art_id: str = Field(
        ...,
        description="The ID of the work of art page on Wikipedia. This is the part of the URL after 'wiki/'",
    )
    other_titles: list[str] | None = Field(
        None,
        description="Other titles of the work of art if any.",
    )
