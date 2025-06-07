from pydantic import BaseModel, Field, HttpUrl

from src.entities.extraction import ExtractionResult
from src.entities.person import PersonCharacteristics
from src.entities.source import SourcedContentBase
from src.repositories.ml.ollama_parser import OllamaExtractor


def test_ollama_is_called_correctly(mocker):

    # given
    base_info = SourcedContentBase(
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

    response = '{"handicaps":["sourd", "aveugle"], "uid": "123", "score": 0.95}'

    mocker.patch(
        "src.repositories.ml.ollama_parser.ollama.chat",
        return_value=MockResponse(MockMessage(response)),
    )

    from src.settings import Settings

    parser = OllamaExtractor(Settings())
    content = "This is a test content for Ollama."
    entity_type = PersonCharacteristics

    # when
    result = parser.extract_entity(
        content,
        entity_type,
        base_info,
    )

    # then
    assert isinstance(result, ExtractionResult)
    assert isinstance(result.entity, PersonCharacteristics)
    assert result.entity.disabilities == ["sourd", "aveugle"]
    assert result.score == 0.95


def test_create_response_model():

    # given
    class MyModel(BaseModel):
        height: int = Field(..., description="Height in centimeters")

    from src.settings import Settings

    parser = OllamaExtractor(Settings())

    # when
    response = parser.create_response_model(MyModel)(score=0.9, height=180)

    # then
    assert response.score == 0.9
    assert response.height == 180
