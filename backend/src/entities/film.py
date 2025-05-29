from pydantic import Field, HttpUrl

from .person import Person
from .woa import WorkOfArt


class Film(WorkOfArt):
    """
    TODO:
    - fix issue with release_date
    """

    # optional
    subtitle: str | None = Field(
        None,
        repr=False,
    )
    summary: str | None = Field(
        None,
        repr=False,
    )
    info: dict | None = Field(
        None,
        description="Misc. information about the film that is not covered by the other fields.",
        repr=False,
    )
    # release_date: datetime | None = Field(
    #     None,
    #     description="The year the film was released",
    # )
    directors: list[str] | None = Field(
        None,
        description="The directors of the film",
        repr=False,
    )
    assistant_directors: list[str] | None = Field(
        None,
        description="The assistant director of the film",
        repr=False,
    )

    distributor: str | None = Field(
        None,
        description="The distributor of the film",
        repr=False,
    )
    country: str | None = Field(
        None,
        examples=["FR", "USA", "UK"],
        description="The country of origin of the film",
        repr=False,
    )

    poster: HttpUrl | None = Field(
        None,
        repr=False,
    )
    other_media: list[HttpUrl] | None = Field(
        None,
        repr=False,
    )
    other_titles: list[str] | None = Field(
        None,
        repr=False,
    )
    trailer: HttpUrl | None = Field(
        None,
        repr=False,
    )
    genres: list[str] | None = Field(
        None,
        repr=False,
    )
    scriptwriters: list[str] | None = Field(
        None,
        description="The scriptwriters of the film",
        repr=False,
    )
    duration: float | None = Field(
        None,
        description="The duration of the film in minutes",
        repr=False,
    )
    main_roles: list[str] | None = Field(
        None,
        description="The main roles of the film",
        repr=False,
    )
    other_roles: list[str] | None = Field(
        None,
        description="The other roles of the film",
        repr=False,
    )
    influencing_works: list[WorkOfArt] | None = Field(
        None,
        description="The work arts that influenced the film",
        examples=["Film 1", "Theatre 1", "Book 1"],
        repr=False,
    )
    influencing_persons: list[Person] | None = Field(
        None,
        description="The personalities that influenced the film",
        examples=["Person 1", "Person 2"],
        repr=False,
    )
