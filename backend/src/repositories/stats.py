import redis
from loguru import logger
from pydantic import RedisDsn

from src.interfaces.stats import IStatsCollector, StatKey


class RedisStatsCollector(IStatsCollector):
    """A simple Redis stats collector implementation."""

    client: redis.Redis
    _key_prefix: str = "stats:"

    def __init__(self, redis_dsn: RedisDsn):
        self.client = redis.Redis(
            host=redis_dsn.host,
            port=redis_dsn.port,
            db=(redis_dsn.path.lstrip("/") if redis_dsn.path else 0),
            username=redis_dsn.username,
            password=redis_dsn.password,
            decode_responses=True,
        )

        logger.info(f"RedisStatsCollector connected to '{redis_dsn}'")

    def _compose_key(self, key: StatKey, flow_id: str) -> str:
        return f"{self._key_prefix}{key}:{flow_id}"

    def get_value(self, key: StatKey, flow_id: str, default: int | None = None) -> int:
        val = self.client.get(self._compose_key(key, flow_id)) or default
        try:
            if val is None:
                return default
            return int(val)
        except (ValueError, TypeError):
            logger.error(f"Failed to convert value '{val}' to int for key '{key}'")
            return default

    def set_value(self, key: StatKey, flow_id: str, value: int) -> None:
        self.client.set(self._compose_key(key, flow_id), value)

    def inc_value(
        self,
        key: StatKey,
        flow_id: str,
        count: int = 1,
        start: int = 0,
    ) -> None:
        if not self.client.exists(self._compose_key(key, flow_id)):
            self.client.set(self._compose_key(key, flow_id), start + count)
        else:
            self.client.incr(self._compose_key(key, flow_id), count)

    def collect(self, flow_id: str) -> dict[str, int]:

        d = {}
        for key in StatKey:
            value = self.get_value(key, flow_id)
            if value is not None and value > 0:
                d[key.name] = value

        return d
