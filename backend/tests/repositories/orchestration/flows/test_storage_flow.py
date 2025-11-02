import meilisearch
import pytest
import redis

from src.entities.person import Person
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.settings import AppSettings
from tests.repositories.orchestration.stubs.stub_storage import StubStorage


@pytest.fixture(scope="function", autouse=True)
def cleanup_redis(test_settings: AppSettings):

    r = redis.Redis.from_url(test_settings.storage_settings.redis_dsn)
    r.flushdb()
    yield
    r.flushdb()


@pytest.fixture(scope="function", autouse=False)
def cleanup_db(test_settings: AppSettings):

    from neo4j import GraphDatabase, Session

    c = GraphDatabase = GraphDatabase.driver(
        str(test_settings.storage_settings.graphdb_uri),
        auth=("", ""),
    )
    session: Session = c.session()
    with session:
        session.run("MATCH (n) DETACH DELETE n")

    meili = meilisearch.Client(
        str(test_settings.search_settings.base_url),
        test_settings.search_settings.api_key,
    )
    meili.delete_index(test_settings.search_settings.persons_index_name)
    meili.delete_index(test_settings.search_settings.movies_index_name)

    yield

    session: Session = c.session()
    with session:
        session.run("MATCH (n) DETACH DELETE n")

    meili.delete_index(test_settings.search_settings.persons_index_name)
    meili.delete_index(test_settings.search_settings.movies_index_name)


def test_entity_storage_flow(test_settings: AppSettings):
    # given
    entity_type = "Person"
    json_store = RedisJsonStorage[Person](test_settings.storage_settings.redis_dsn)

    # generate a Person entity into the json_store
    person = Person(
        title="Ludwig van Beethoven",
        permalink="https://en.wikipedia.org/wiki/Ludwig_van_Beethoven",
    )

    json_store.insert(person.uid, person)

    db_store = PersonGraphRepository(settings=test_settings.storage_settings)
    assert len(list(db_store.scan())) == 0

    # not interesting for this test
    search_store = StubStorage[Person]()

    # when
    db_storage_flow(
        app_settings=test_settings,
        entity_type=entity_type,
        json_store=json_store,
        graph_store=db_store,
        search_store=search_store,
        refresh_cache=True,  # force re-processing of all pages
    )

    # then
    # the entity is now in the DB
    assert len(list(db_store.scan())) == 1
    stored_person_uid = list(db_store.scan())[0][0]

    assert stored_person_uid == person.uid
