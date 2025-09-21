from src.entities.composable import Composable
from src.entities.ml import ExtractionResult
from src.entities.person import Biography
from src.repositories.ml.ollama_generic import GenericOllamaExtractor
from src.settings import Settings


def test_parent_uid_is_attached_to_entity(mocker, test_settings: Settings):
    # given
    base_info = Composable(
        title="Test Title",
        permalink="http://example.com/test",
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
        '{"score": 0.95, "parent_uid": "test_uid", "nom_complet": "John Doe"}'
    )

    # suppose Ollama chat responds with a JSON string
    mocker.patch(
        "src.repositories.ml.ollama_messager.ollama.chat",
        return_value=MockResponse(MockMessage(mock_llm_response)),
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
