
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.entities.person import Person
from src.interfaces.assembler import IEntityAssembler

from .woa import WOAInfluence, WOASpecifications, WOAType, WorkOfArt


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
    directed_by: list[Person] | None = Field(
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


class FilmAssembler(IEntityAssembler[Film]):
    """
    Assembler for Film entities.
    """

    def assemble(self, uid: str, title: str, parts: list[BaseModel]) -> Film:
        """
        Assemble the Film entity from the provided data.

        TODO:
        - try / catch to handle cases where the parts do not match the expected types.
        - testing

        Args:
            parts (list[BaseModel]): A list of BaseModel instances that represent the content to be assembled.
                Each part should conform to the structure defined by the Film entity.

        Returns:
            Film: The assembled Film entity.
        """

        _film = Film(
            uid=uid,
            title=title,
            woa_type=WOAType.FILM,  # Assuming "film" is a valid WOAType
        )

        for part in parts:
            if isinstance(part, FilmSummary):
                _film.summary = part
            elif isinstance(part, FilmMedia):
                _film.media = part
            elif isinstance(part, FilmSpecifications):
                _film.specifications = part
            elif isinstance(part, FilmActor):
                if _film.actors is None:
                    _film.actors = []
                _film.actors.append(part)
            elif isinstance(part, WOAInfluence):
                if _film.influences is None:
                    _film.influences = []
                _film.influences.append(part)
            else:
                raise ValueError(f"Unsupported part type: {type(part)}")

        return _film
