import meilisearch
import pytest
import redis

from src.entities.person import Person
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.settings import Settings


@pytest.fixture(scope="function", autouse=True)
def cleanup_redis(test_settings: Settings):

    r = redis.Redis(
        host=test_settings.redis_storage_dsn.host,
        port=test_settings.redis_storage_dsn.port,
        db=(
            test_settings.redis_storage_dsn.path.lstrip("/")
            if test_settings.redis_storage_dsn.path
            else 0
        ),
        username=test_settings.redis_storage_dsn.username,
        password=test_settings.redis_storage_dsn.password,
        decode_responses=True,
    )
    r.flushdb()
    yield
    r.flushdb()


@pytest.fixture(scope="function", autouse=True)
def cleanup_db(test_settings: Settings):

    from neo4j import GraphDatabase, Session

    c = GraphDatabase = GraphDatabase.driver(
        str(test_settings.graph_db_uri),
        auth=("", ""),
    )
    session: Session = c.session()
    with session:
        session.run("MATCH (n) DETACH DELETE n")

    meili = meilisearch.Client(
        str(test_settings.search_base_url), test_settings.search_api_key
    )
    meili.delete_index(test_settings.search_persons_index_name)
    meili.delete_index(test_settings.search_movies_index_name)

    yield

    session: Session = c.session()
    with session:
        session.run("MATCH (n) DETACH DELETE n")

    meili.delete_index(test_settings.search_persons_index_name)
    meili.delete_index(test_settings.search_movies_index_name)


def test_entity_storage_flow(test_settings: Settings):
    # given
    entity_type = "Person"
    json_store = RedisJsonStorage[Person](settings=test_settings)

    # generate a Person entity into the json_store
    person = Person(
        title="Ludwig van Beethoven",
        permalink="https://en.wikipedia.org/wiki/Ludwig_van_Beethoven",
    )

    json_store.insert(person.uid, person)

    db_store = PersonGraphRepository(settings=test_settings)
    assert len(list(db_store.scan())) == 0

    # when
    db_storage_flow(
        settings=test_settings,
        entity_type=entity_type,
        json_store=json_store,
        graph_store=db_store,
    )

    # then
    # the entity is now in the DB
    assert len(list(db_store.scan())) == 1
    stored_person_uid = list(db_store.scan())[0][0]

    assert stored_person_uid == person.uid
