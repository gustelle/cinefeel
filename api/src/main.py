import strawberry

from src.queries.movies import MovieQuery

schema = strawberry.Schema(query=MovieQuery)
