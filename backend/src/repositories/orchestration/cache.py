from prefect.cache_policies import (
    INPUTS,
)
from prefect.transactions import IsolationLevel
from prefect_redis import RedisLockManager
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings


class CacheSettings(BaseSettings):
    prefect_cache_redis_dsn: RedisDsn = Field(
        default="redis://localhost:6379/2",
    )


_cache_settings = CacheSettings()

CACHE_POLICY = INPUTS.configure(
    isolation_level=IsolationLevel.SERIALIZABLE,
    lock_manager=RedisLockManager(
        host=_cache_settings.prefect_cache_redis_dsn.host,
        port=_cache_settings.prefect_cache_redis_dsn.port,
        db=(
            _cache_settings.prefect_cache_redis_dsn.path.lstrip("/")
            if _cache_settings.prefect_cache_redis_dsn.path
            else 0
        ),
        username=_cache_settings.prefect_cache_redis_dsn.username,
        password=_cache_settings.prefect_cache_redis_dsn.password,
        ssl=_cache_settings.prefect_cache_redis_dsn.scheme == "rediss",
    ),
)
