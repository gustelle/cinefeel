from asyncio import Protocol
from enum import StrEnum


class StatKey(StrEnum):

    SCRAPING_SUCCESS = "scraping_success"
    SCRAPING_FAILED = "scraping_failed"
    SCRAPING_VOID = "scraping_void"
    EXTRACTION_SUCCESS = "extraction_success"
    EXTRACTION_FAILED = "extraction_failed"
    EXTRACTION_VOID = "extraction_void"


class IStatsCollector(Protocol):
    """inspired by scrapy stats collector"""

    def get_value(self, key: StatKey, flow_id: str, default: int | None = None) -> int:
        raise NotImplementedError("This method should be overridden by subclasses.")

    def set_value(self, key: StatKey, flow_id: str, value: int) -> None:
        raise NotImplementedError("This method should be overridden by subclasses.")

    def inc_value(
        self,
        key: StatKey,
        flow_id: str,
        count: int = 1,
        start: int = 0,
    ) -> None:
        raise NotImplementedError("This method should be overridden by subclasses.")

    def collect(self, flow_id: str) -> dict[str, int]:
        raise NotImplementedError("This method should be overridden by subclasses.")
