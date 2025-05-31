from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .woa import WOAInfluence, WOASpecifications, WorkOfArt


class FilmActor(BaseModel):
    full_name: str = Field(
        ...,
        description="The full name of the actor.",
        examples=["John Doe", "Jane Smith"],
        repr=False,
    )
    roles: list[str] | None = Field(
        None,
        description="The list of roles played by the actor in the film.",
        examples=[
            ["Hero", "Villain"],
            ["Supporting Actor"],
            ["Lead Role", "Cameo"],
        ],
        repr=False,
    )


class FilmSummary(BaseModel):
    """ """

    content: str | None = Field(
        None,
        description="The summary of the film.",
        examples=["A thrilling adventure through time and space."],
        repr=False,
    )
    source: str | None = Field(
        None,
        description="The source URL of the summary.",
        examples=["https://example.com/film-summary"],
        repr=False,
    )


class FilmMedia(BaseModel):
    """ """

    poster: str | None = Field(
        None,
        repr=False,
    )
    other_media: list[str] | None = Field(
        None,
        repr=False,
    )
    trailer: HttpUrl | None = Field(
        None,
        repr=False,
    )


class FilmSpecifications(WOASpecifications):
    directed_by: list[str] | None = Field(
        None,
        repr=False,
    )
    produced_by: list[str] | None = Field(
        None,
        repr=False,
    )
    genres: list[str] | None = Field(
        None,
        repr=False,
    )
    special_effects_by: list[str] | None = Field(
        None,
        repr=False,
    )
    scenary_by: list[str] | None = Field(
        None,
        repr=False,
    )
    written_by: list[str] | None = Field(
        None,
        repr=False,
    )
    music_by: list[str] | None = Field(
        None,
        repr=False,
    )
    duration: str | None = Field(
        None,
        description="The duration of the film in HH:MM:SS format.",
        examples=["01:30:00", "02:15:45"],
        repr=False,
    )


class Film(WorkOfArt):
    """ """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str = Field(
        ...,
        description="The title of the film.",
        examples=["Inception", "The Matrix"],
    )

    summary: FilmSummary | None = Field(
        None,
        repr=False,
    )
    media: FilmMedia | None = Field(
        None,
        repr=False,
    )
    influences: list[WOAInfluence] | None = Field(
        None,
        repr=False,
    )
    specifications: FilmSpecifications | None = Field(
        None,
        repr=False,
    )
    actors: list[FilmActor] | None = Field(
        None,
        repr=False,
    )
