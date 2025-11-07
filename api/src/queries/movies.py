import typing

import strawberry

from src.entities.movie import Movie


def get_movies():
    return [
        Movie(
            title="Inception",
        ),
    ]


@strawberry.type
class MovieQuery:
    movies: typing.List[Movie] = strawberry.field(resolver=get_movies)
