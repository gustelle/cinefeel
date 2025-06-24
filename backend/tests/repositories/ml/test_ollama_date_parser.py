from src.repositories.ml.ollama_date_parser import OllamaDateFormatter
from src.settings import Settings


def test_ollama_date_formatter():

    formatter = OllamaDateFormatter(settings=Settings())
    birth_date = "25 octobre 1852 à Paris 10ème, France"
    resp = formatter.format(
        content=birth_date,
    )
    assert resp == "1852-10-25", f"Expected '1852-10-25', got '{resp}'"
