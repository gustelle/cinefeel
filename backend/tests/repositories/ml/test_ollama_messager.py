from src.entities.composable import Composable
from src.entities.ml import ExtractionResult
from src.entities.person import Biography
from src.repositories.ml.ollama_generic import GenericOllamaExtractor
from src.settings import Settings

from .stub.stub_llm import OllamaMessage, StubOllama


def test_parent_uid_is_attached_to_entity(mocker, test_settings: Settings):
    # given
    base_info = Composable(
        title="Test Title",
        permalink="http://example.com/test",
    )

    mock_llm_response = (
        '{"score": 0.95, "parent_uid": "test_uid", "full_name": "John Doe"}'
    )

    # suppose Ollama chat responds with a JSON string
    mocker.patch(
        "src.repositories.ml.ollama_messager.ollama.chat",
        return_value=StubOllama(OllamaMessage(mock_llm_response)),
    )

    parser = GenericOllamaExtractor(test_settings)
    entity_type = Biography

    # when
    result = parser.request_entity(
        "",
        entity_type,
        base_info,
    )

    # then
    assert isinstance(result, ExtractionResult)
    assert isinstance(result.entity, Biography)
    assert result.entity.parent_uid == base_info.uid
    assert result.score == 0.95
