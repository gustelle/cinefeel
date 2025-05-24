
from pydantic import Field, HttpUrl

from .person import Person
from .woa import WorkOfArt


class Film(WorkOfArt):
    """
    TODO:
    - manage genres etc...
    - fix issue with datetime
    """

    # optional
    subtitle: str | None = None
    summary: str | None = None
    info: dict | None = Field(
        None,
        description="Misc. information about the film that is not covered by the other fields.",
    )
    # release_date: datetime | None = Field(
    #     None,
    #     description="The year the film was released",
    # )
    directors: list[str] | None = Field(
        None,
        description="The directors of the film",
    )
    assistant_directors: list[str] | None = Field(
        None,
        description="The assistant director of the film",
    )

    distributor: str | None = Field(
        None,
        description="The distributor of the film",
    )
    country: str | None = Field(
        None,
        examples=["FR", "USA", "UK"],
        description="The country of origin of the film",
    )

    poster: HttpUrl | None = None
    other_media: list[HttpUrl] | None = None
    other_titles: list[str] | None = None
    trailer: HttpUrl | None = None
    genres: list[str] | None = None
    scriptwriters: list[str] | None = Field(
        None,
        description="The scriptwriters of the film",
    )
    duration: float | None = Field(
        None,
        description="The duration of the film in minutes",
    )
    main_roles: list[str] | None = Field(
        None,
        description="The main roles of the film",
    )
    other_roles: list[str] | None = Field(
        None,
        description="The other roles of the film",
    )
    influencing_works: list[WorkOfArt] | None = Field(
        None,
        description="The work arts that influenced the film",
        examples=["Film 1", "Theatre 1", "Book 1"],
    )
    influencing_persons: list[Person] | None = Field(
        None,
        description="The personalities that influenced the film",
        examples=["Person 1", "Person 2"],
    )
