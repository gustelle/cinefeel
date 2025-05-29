from src.entities.film import Film
from src.interfaces.analyzer import IContentAnalyzer


class StubAnalyzer(IContentAnalyzer[Film]):

    is_analyzed: bool = False

    def analyze(self, *args, **kwargs) -> Film:
        # This is a stub method that simulates analysis
        self.is_analyzed = True
        return Film(
            title="Stub Film",
            uid="stub_film_id",
        )
