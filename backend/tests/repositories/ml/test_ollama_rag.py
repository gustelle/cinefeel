from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.ml import ExtractionResult
from src.entities.person import Biography
from src.repositories.ml.ollama_generic import GenericOllamaExtractor
from src.settings import AppSettings

from .stub.stub_llm import OllamaMessage, StubOllama


def test_ollama_is_called_correctly(mocker, test_settings: AppSettings):

    # given
    base_info = Composable(
        uid="test_uid",
        title="Test Title",
        permalink=HttpUrl("http://example.com/test"),
    )

    mock_llm_response = '{"full_name": "Quentin Jerome Tarantino", "uid": "123", "score": 0.95, "parent_uid": "test_uid"}'

    # suppose Ollama chat responds with a JSON string
    mocker.patch(
        "src.repositories.ml.ollama_messager.ollama.chat",
        return_value=StubOllama(OllamaMessage(mock_llm_response)),
    )

    parser = GenericOllamaExtractor(test_settings.ml_settings)
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
