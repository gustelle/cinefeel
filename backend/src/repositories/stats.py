from contextlib import contextmanager

import redis
from loguru import logger

from src.interfaces.stats import IStatsCollector, StatKey


class RedisStatsCollector(IStatsCollector):
    """A simple Redis stats collector implementation."""

    _key_prefix: str = "stats:"
    redis_dsn: str

    def __init__(self, redis_dsn: str):
        """for serialization purposes, we store the dsn as a string not as a `RedisDsn` object"""
        self.redis_dsn = redis_dsn

    @contextmanager
    def client(self):
        _client = redis.Redis.from_url(self.redis_dsn, decode_responses=True)
        try:
            yield _client
        finally:
            _client.close()

    def on_init(self):
        pass

    def _compose_key(self, key: StatKey, flow_id: str) -> str:
        return f"{self._key_prefix}{key}:{flow_id}"

    def get_value(self, key: StatKey, flow_id: str, default: int | None = None) -> int:

        with self.client() as _client:

            val = _client.get(self._compose_key(key, flow_id)) or default
            try:
                if val is None:
                    return default
                return int(val)
            except (ValueError, TypeError):
                logger.error(f"Failed to convert value '{val}' to int for key '{key}'")
                return default

    def set_value(self, key: StatKey, flow_id: str, value: int) -> None:

        with self.client() as _client:
            _client.set(self._compose_key(key, flow_id), value)

    def inc_value(
        self,
        key: StatKey,
        flow_id: str,
        count: int = 1,
        start: int = 0,
    ) -> None:

        with self.client() as _client:

            if not _client.exists(self._compose_key(key, flow_id)):
                _client.set(self._compose_key(key, flow_id), start + count)
            else:
                _client.incr(self._compose_key(key, flow_id), count)

    def collect(self, flow_id: str) -> dict[str, int]:

        d = {}
        for key in StatKey:
            value = self.get_value(key, flow_id)
            if value is not None and value > 0:
                d[key.name] = value

        return d
