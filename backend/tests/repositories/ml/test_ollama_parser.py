from pydantic import BaseModel, Field

from src.entities.person import PersonCharacteristics
from src.interfaces.extractor import ExtractionResult
from src.repositories.ml.ollama_parser import OllamaExtractor


def test_ollama_is_called_correctly(mocker):

    # given

    class MockMessage:
        content: str

        def __init__(self, content):
            self.content = content

    class MockResponse:

        message: MockMessage

        def __init__(self, message):
            self.message = message

    response = '{"handicaps":["sourd", "aveugle"], "score": 0.95}'

    mocker.patch(
        "src.repositories.ml.ollama_parser.ollama.chat",
        return_value=MockResponse(MockMessage(response)),
    )

    from src.settings import Settings

    parser = OllamaExtractor(Settings())
    content = "This is a test content for Ollama."
    entity_type = PersonCharacteristics

    # when
    result = parser.extract_entity(content, entity_type)

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
