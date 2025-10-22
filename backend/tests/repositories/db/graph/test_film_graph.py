import uuid

from neo4j import GraphDatabase
from neo4j.graph import Node

from src.entities.movie import FilmSpecifications, Movie
from src.entities.person import Person
from src.entities.relationship import (
    PeopleRelationshipType,
    StrongRelationship,
    WOARelationshipType,
)
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository


def test_insert_a_film(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
):
    """assert the data type is correct when inserting a film"""

    # given
    # drop all existing data

    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")

    # when
    count = test_film_graphdb.insert_many([test_film])

    # then
    assert count == 1  # Only one film should be inserted

    # select the film to verify its type
    records, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Movie {{uid: '{test_film.uid}'}})
        RETURN n LIMIT 1;
        """
    )
    film_data: Node = records[0].get("n", {})

    assert film_data is not None
    assert "uid" in film_data
    assert "title" in film_data
    assert "permalink" in film_data
    assert "media" in film_data
    assert "influences" in film_data
    assert "specifications" in film_data
    assert "actors" in film_data

    for field, value in film_data.items():
        if field == "uid":
            assert isinstance(value, str)
        elif field == "title":
            assert isinstance(value, str)
        elif field == "permalink":
            assert isinstance(value, str)
        elif field in ["media"]:
            assert (
                isinstance(value, dict)
                and "posters" in value
                and isinstance(value["posters"], list)
            )
        elif field in ["influences"]:
            assert isinstance(value, list) and all(
                isinstance(item, dict) for item in value
            )
        elif field in ["specifications"]:
            assert (
                isinstance(value, dict)
                and "written_by" in value
                and isinstance(value["written_by"], list)
            )
        elif field in ["actors"]:
            assert isinstance(value, list) and all(
                isinstance(actor, dict) for actor in value
            )

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_insert_several_films(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
):
    """assert several films can be inserted at once"""

    # given
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")

    dict_film = test_film.model_dump()
    dict_film["title"] = f"{test_film.title} Copy"

    other_film = Movie(**dict_film)

    # when
    count = test_film_graphdb.insert_many([test_film, other_film])

    # then
    assert count == 2  # Two films should be inserted

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_update_a_film(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
):
    """assert a film can be updated if it already exists in the database"""

    # given
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")
    test_film_graphdb.insert_many([test_film])

    # when
    updated_film = test_film.model_copy(deep=True)
    updated_film.title = "Inception (Updated)"
    c = test_film_graphdb.insert_many([updated_film])

    # then
    assert c == 1  # Only one film should be updated
    # check if the film was updated
    records, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Movie {{uid: '{updated_film.uid}'}})
        RETURN n LIMIT 1;
        """
    )
    film_data: Node = records[0].get("n", {})
    assert film_data is not None
    assert film_data.get("title") == "Inception (Updated)"

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_insert_film_deduplication(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")

    # when
    count = test_film_graphdb.insert_many([test_film, test_film])

    # This should not create a duplicate entry
    # then
    assert count == 1  # Only one film should be inserted

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_get_nominal(
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
    test_memgraph_client: GraphDatabase,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")
    test_film_graphdb.insert_many([test_film])

    # when
    retrieved_film = test_film_graphdb.select(test_film.uid)

    # then
    assert retrieved_film is not None
    assert retrieved_film.uid == test_film.uid
    assert retrieved_film.title == test_film.title
    assert retrieved_film.permalink == test_film.permalink
    assert retrieved_film.media == test_film.media
    assert retrieved_film.influences == test_film.influences
    assert retrieved_film.specifications == test_film.specifications
    assert retrieved_film.actors == test_film.actors

    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_get_non_existent(test_film_graphdb: MovieGraphRepository):
    # given

    non_existent_uid = uuid.uuid4().hex

    # when
    retrieved_film = test_film_graphdb.select(non_existent_uid)

    # then
    assert retrieved_film is None


def test_get_bad_data(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
):
    # given
    # insert bad data
    test_memgraph_client.execute_query(
        """
        CREATE (node:Movie {property: 42})
        """
    )

    # when
    result = test_film_graphdb.select("bad-uid")
    # then
    assert result is None

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_add_relationship_to_person(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
    test_person_graphdb: PersonGraphRepository,
    test_person: Person,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")
    test_film_graphdb.insert_many([test_film])
    test_person_graphdb.insert_many([test_person])

    # when
    test_film_graphdb.add_relationship(
        relationship=StrongRelationship(
            from_entity=test_film,
            to_entity=test_person,
            relation_type=PeopleRelationshipType.DIRECTED_BY,
        )
    )

    # then
    # verify the relationship was created
    results, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Movie {{uid: $from_uid}})-[r:{str(PeopleRelationshipType.DIRECTED_BY)}]->(m:Person {{uid: $to_uid}})
        RETURN r
        """,
        from_uid=test_film.uid,
        to_uid=test_person.uid,
    )

    assert len(results) == 1

    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")


def test_add_relationship_to_film(
    test_memgraph_client: GraphDatabase,
    test_film_graphdb: MovieGraphRepository,
    test_film: Movie,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")

    dict_film = test_film.model_dump()
    dict_film["title"] = "Inception Copy"

    film_copy = Movie(**dict_film)

    assert film_copy.uid != test_film.uid  # Ensure it's a different instance
    test_film_graphdb.insert_many([test_film, film_copy])

    # when
    test_film_graphdb.add_relationship(
        relationship=StrongRelationship(
            from_entity=test_film,
            to_entity=film_copy,
            relation_type=WOARelationshipType.INSPIRED_BY,
        )
    )

    # then
    # verify the relationship was created
    results, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Movie {{uid: $from_uid}})-[r:{str(WOARelationshipType.INSPIRED_BY)}]->(m:Movie {{uid: $to_uid}})
        RETURN r
        """,
        from_uid=test_film.uid,
        to_uid=film_copy.uid,
    )

    assert len(results) == 1

    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")


def test_select_film(
    test_film_graphdb: MovieGraphRepository,
    test_memgraph_client: GraphDatabase,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")
    film = Movie(
        title="Inception",
        permalink="https://example.com/inception",
    )
    specifications = FilmSpecifications(
        parent_uid=film.uid,
        title="Inception",
        duration=148,
        release_date="2010-07-16",
        genres=["Science Fiction", "Action"],
        written_by=["Christopher Nolan"],
    )
    film.specifications = specifications

    test_film_graphdb.insert_many([film])

    # when
    retrieved_film = test_film_graphdb.select(film.uid)

    # then
    assert retrieved_film is not None
    assert retrieved_film.specifications.duration == specifications.duration
    assert retrieved_film.specifications.release_date == specifications.release_date
    assert retrieved_film.specifications.genres == specifications.genres
    assert retrieved_film.specifications.written_by == specifications.written_by

    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")


def test_get_related(
    test_film_graphdb: MovieGraphRepository,
    test_memgraph_client: GraphDatabase,
    test_person_graphdb: PersonGraphRepository,
    test_film: Movie,
    test_person: Person,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")

    film_copy = test_film.model_copy(deep=True)
    film_copy.title = "Inception Copy"

    test_film_graphdb.insert_many([test_film, film_copy])
    test_person_graphdb.insert_many([test_person])

    test_film_graphdb.add_relationship(
        relationship=StrongRelationship(
            from_entity=test_film,
            to_entity=test_person,
            relation_type=PeopleRelationshipType.DIRECTED_BY,
        )
    )

    test_film_graphdb.add_relationship(
        relationship=StrongRelationship(
            from_entity=test_film,
            to_entity=film_copy,
            relation_type=WOARelationshipType.INSPIRED_BY,
        )
    )

    # when
    related = test_film_graphdb.get_related(test_film)

    # then
    assert len(related) == 2
    assert any(
        rel.from_entity.uid == test_film.uid
        and rel.to_entity.uid == test_person.uid
        and rel.relation_type == PeopleRelationshipType.DIRECTED_BY
        for rel in related
    )
    assert any(
        rel.from_entity.uid == test_film.uid
        and rel.to_entity.uid == film_copy.uid
        and rel.relation_type == WOARelationshipType.INSPIRED_BY
        for rel in related
    )

    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")


def test_get_related_with_relation_type(
    test_film_graphdb: MovieGraphRepository,
    test_memgraph_client: GraphDatabase,
    test_person_graphdb: PersonGraphRepository,
    test_film: Movie,
    test_person: Person,
):

    # given
    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")

    film_copy = test_film.model_copy(deep=True)
    film_copy.title = "Inception Copy"

    test_film_graphdb.insert_many([test_film, film_copy])
    test_person_graphdb.insert_many([test_person])

    test_film_graphdb.add_relationship(
        relationship=StrongRelationship(
            from_entity=test_film,
            to_entity=test_person,
            relation_type=PeopleRelationshipType.DIRECTED_BY,
        )
    )

    test_film_graphdb.add_relationship(
        relationship=StrongRelationship(
            from_entity=test_film,
            to_entity=film_copy,
            relation_type=WOARelationshipType.INSPIRED_BY,
        )
    )

    # when
    related = test_film_graphdb.get_related(
        test_film, relation_type=PeopleRelationshipType.DIRECTED_BY
    )

    # then
    assert len(related) == 1
    assert any(
        rel.from_entity.uid == test_film.uid
        and rel.to_entity.uid == test_person.uid
        and rel.relation_type == PeopleRelationshipType.DIRECTED_BY
        for rel in related
    )

    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")


def test_graph_scan(
    test_film_graphdb: MovieGraphRepository,
    test_memgraph_client: GraphDatabase,
    test_person_graphdb: PersonGraphRepository,
    test_film: Movie,
    test_person: Person,
):

    # given
    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")

    films = [test_film]

    for i in range(5):
        film_copy = test_film.model_copy(deep=True)
        film_copy.title = f"Inception Copy {i}"
        films.append(film_copy)

    test_film_graphdb.insert_many(films)

    persons = [test_person]

    for i in range(5):
        person_copy = test_person.model_copy(deep=True)
        person_copy.title = f"Person Copy {i}"
        persons.append(person_copy)

    test_person_graphdb.insert_many(persons)

    # when
    results = list(test_film_graphdb.scan())

    assert len(results) == 6  # 1 original + 5 copies
    assert all(
        isinstance(item[1], Movie) for item in results
    )  # there is no person in the scan

    test_memgraph_client.execute_query("MATCH (n:Movie), (m:Person) DETACH DELETE n, m")


def test_query_graph_by_permalink(
    test_film_graphdb: MovieGraphRepository,
    test_memgraph_client: GraphDatabase,
    test_person_graphdb: PersonGraphRepository,
    test_film: Movie,
    test_person: Person,
):
    # given
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")

    films = [test_film]

    for i in range(5):
        film_copy = test_film.model_copy(deep=True)
        film_copy.title = f"Inception Copy {i}"
        film_copy.permalink = f"https://example.com/inception-copy-{i}"
        films.append(film_copy)

    test_film_graphdb.insert_many(films)

    persons = [test_person]

    for i in range(5):
        person_copy = test_person.model_copy(deep=True)
        person_copy.title = f"Person Copy {i}"

        persons.append(person_copy)

    test_person_graphdb.insert_many(persons)

    # when
    results = test_film_graphdb.query(permalink=test_film.permalink)

    # then
    assert len(results) == 1
    assert isinstance(results[0], Movie)
    assert results[0].uid == test_film.uid

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Movie) DETACH DELETE n")
