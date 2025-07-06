from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.ml import ExtractionResult
from src.entities.person import Biography
from src.repositories.ml.ollama_generic import GenericInfoExtractor
from src.settings import Settings


def test_ollama_is_called_correctly(mocker):

    # given
    base_info = Composable(
        uid="test_uid",
        title="Test Title",
        permalink=HttpUrl("http://example.com/test"),
    )

    class MockMessage:
        content: str

        def __init__(self, content):
            self.content = content

    class MockResponse:

        message: MockMessage

        def __init__(self, message):
            self.message = message

    mock_llm_response = (
        '{"nom_complet": "Quentin Jerome Tarantino", "uid": "123", "score": 0.95}'
    )

    # suppose Ollama chat responds with a JSON string
    mocker.patch(
        "src.repositories.ml.ollama_messager.ollama.chat",
        return_value=MockResponse(MockMessage(mock_llm_response)),
    )

    parser = GenericInfoExtractor(Settings())
    content = "This is a test content for Ollama."
    entity_type = Biography

    # when
    result = parser.extract_entity(
        content,
        None,  # No media for this test
        entity_type,
        base_info,
    )

    # then
    assert isinstance(result, ExtractionResult)
    assert isinstance(result.entity, Biography)
    assert result.entity.full_name == "Quentin Jerome Tarantino"
    assert result.score == 0.95
