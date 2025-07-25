from neo4j import GraphDatabase
from neo4j.graph import Node

from src.entities.person import Biography, Person
from src.repositories.db.person_graph import PersonGraphHandler


def test_insert_a_person(
    test_memgraph_client: GraphDatabase,
    test_person_handler: PersonGraphHandler,
    test_person: Person,
):
    """assert the data type is correct when inserting a person"""

    # given
    # drop all existing data

    test_memgraph_client.execute_query("MATCH (n:Person) DETACH DELETE n")

    # when
    count = test_person_handler.insert_many([test_person])

    # then
    assert count == 1  # Only one person should be inserted

    # select the person to verify its type
    records, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Person {{uid: '{test_person.uid}'}})
        RETURN n LIMIT 1;
        """
    )
    person_data: Node = records[0].get("n", {})

    assert person_data is not None
    assert "uid" in person_data
    assert "title" in person_data
    assert "permalink" in person_data
    assert "biography" in person_data
    assert isinstance(person_data["biography"], dict)
    assert "full_name" in person_data["biography"]
    assert person_data["biography"]["full_name"] == test_person.biography.full_name
    assert "characteristics" in person_data
    assert isinstance(person_data["characteristics"], dict)
    assert "influences" in person_data
    assert isinstance(person_data["influences"], list)

    # tear down the database
    test_memgraph_client.execute_query("MATCH (n:Person) DETACH DELETE n")


def test_select_person(
    test_person_handler: PersonGraphHandler, test_memgraph_client: GraphDatabase
):
    # given

    test_memgraph_client.execute_query("MATCH (n:Person) DETACH DELETE n")

    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )
    bio = Biography(
        parent_uid=person.uid,
        full_name="Christopher Nolan",
    )
    person.biography = bio

    test_person_handler.insert_many([person])

    # when
    retrieved_person = test_person_handler.select(person.uid)

    # then
    assert retrieved_person is not None
    assert retrieved_person.biography.full_name == bio.full_name
    assert retrieved_person.title == person.title
    assert retrieved_person.permalink == person.permalink

    test_memgraph_client.execute_query("MATCH (n:Person) DETACH DELETE n")
