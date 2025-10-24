import uuid

import redis

from src.repositories.stats import RedisStatsCollector, StatKey
from src.settings import Settings


def test_redis_stats_collector_get_value_not_existing(test_settings: Settings):

    # given
    redis_dsn = test_settings.redis_stats_dsn
    collector = RedisStatsCollector(redis_dsn=redis_dsn)
    redis_client = redis.Redis(
        host=redis_dsn.host,
        port=redis_dsn.port,
        db=2,
        username=redis_dsn.username,
        password=redis_dsn.password,
        decode_responses=True,
    )

    test_key = StatKey.SCRAPING_FAILED
    flow_id = str(uuid.uuid4())
    key = collector._compose_key(test_key, flow_id)

    # Ensure the key does not exist
    redis_client.delete(key)

    # Test get_value with default
    assert collector.get_value(test_key, flow_id=flow_id, default=0) == 0

    redis_client.delete(key)


def test_redis_stats_collector_get_existing_value(test_settings: Settings):
    # given
    redis_dsn = test_settings.redis_stats_dsn
    collector = RedisStatsCollector(redis_dsn=redis_dsn)
    redis_client = redis.Redis(
        host=redis_dsn.host,
        port=redis_dsn.port,
        db=2,
        username=redis_dsn.username,
        password=redis_dsn.password,
        decode_responses=True,
    )

    test_key = StatKey.SCRAPING_FAILED
    flow_id = str(uuid.uuid4())

    # Ensure the key does not exist
    key = collector._compose_key(test_key, flow_id)
    redis_client.set(key, 1)

    # when
    val = collector.get_value(test_key, flow_id=flow_id, default=0)

    # Then
    assert val == 1
    redis_client.delete(test_key)


def test_redis_stats_collector_set_value(test_settings: Settings):
    # given
    redis_dsn = test_settings.redis_stats_dsn
    collector = RedisStatsCollector(redis_dsn=redis_dsn)
    redis_client = redis.Redis(
        host=redis_dsn.host,
        port=redis_dsn.port,
        db=2,
        username=redis_dsn.username,
        password=redis_dsn.password,
        decode_responses=True,
    )

    test_key = StatKey.SCRAPING_FAILED
    flow_id = str(uuid.uuid4())
    key = collector._compose_key(test_key, flow_id)

    # Ensure the key does not exist
    redis_client.delete(key)

    # when
    collector.set_value(test_key, flow_id=flow_id, value=42)

    # Then
    assert int(redis_client.get(key)) == 42
    redis_client.delete(key)


def test_redis_stats_collector_inc_value(test_settings: Settings):
    # given
    redis_dsn = test_settings.redis_stats_dsn
    collector = RedisStatsCollector(redis_dsn=redis_dsn)
    redis_client = redis.Redis(
        host=redis_dsn.host,
        port=redis_dsn.port,
        db=2,
        username=redis_dsn.username,
        password=redis_dsn.password,
        decode_responses=True,
    )

    test_key = StatKey.SCRAPING_FAILED
    flow_id = str(uuid.uuid4())
    key = collector._compose_key(test_key, flow_id)

    # Ensure the key does not exist
    redis_client.delete(key)

    # when
    collector.inc_value(test_key, flow_id=flow_id, count=5, start=10)

    # Then
    assert int(redis_client.get(key)) == 15

    # when
    collector.inc_value(test_key, flow_id=flow_id, count=3)

    # Then
    assert int(redis_client.get(key)) == 18

    redis_client.delete(key)


def test_redis_stats_collector_collect(test_settings: Settings):
    # given
    redis_dsn = test_settings.redis_stats_dsn
    collector = RedisStatsCollector(redis_dsn=redis_dsn)
    redis_client = redis.Redis(
        host=redis_dsn.host,
        port=redis_dsn.port,
        db=2,
        username=redis_dsn.username,
        password=redis_dsn.password,
        decode_responses=True,
    )

    flow_id = str(uuid.uuid4())

    # Ensure the keys do not exist
    for key in StatKey:
        redis_client.delete(collector._compose_key(key, flow_id))

    # set some values
    collector.set_value(StatKey.SCRAPING_SUCCESS, flow_id, 10)
    collector.set_value(StatKey.SCRAPING_FAILED, flow_id, 2)
    collector.set_value(StatKey.EXTRACTION_SUCCESS, flow_id, 5)

    # when
    stats = collector.collect(flow_id=flow_id)

    # Then
    assert stats == {
        "SCRAPING_SUCCESS": 10,
        "SCRAPING_FAILED": 2,
        "EXTRACTION_SUCCESS": 5,
    }

    # cleanup
    for key in StatKey:
        redis_client.delete(collector._compose_key(key, flow_id))
