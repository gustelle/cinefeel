from src.interfaces.stats import IStatsCollector, StatKey


class StubStatsCollector(IStatsCollector):

    def __init__(self) -> None:
        self.data: dict[StatKey, int] = {}

    def get_value(self, key: StatKey, flow_id: str, default: int | None = None) -> int:
        return self.data.get(key, default)

    def set_value(self, key: StatKey, flow_id: str, value: int) -> None:
        self.data[key] = value

    def inc_value(
        self,
        key: StatKey,
        flow_id: str,
        count: int = 1,
        start: int = 0,
    ) -> None:
        self.data[key] = self.data.get(key, start) + count

    def collect(self, flow_id: str) -> dict[str, int]:

        return {key.value: value for key, value in self.data.items()}
