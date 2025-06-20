from pydantic import BaseModel, Field, HttpUrl

from src.entities.extraction import ExtractionResult
from src.entities.person import PersonCharacteristics
from src.entities.source import SourcedContentBase
from src.repositories.ml.ollama_parser import OllamaExtractor
from src.settings import Settings


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

    mock_llm_response = (
        '{"handicaps":["sourd", "aveugle"], "uid": "123", "score": 0.95}'
    )

    mocker.patch(
        "src.repositories.ml.ollama_parser.ollama.chat",
        return_value=MockResponse(MockMessage(mock_llm_response)),
    )

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


def test_create_response_model_excludes_http_fields():

    # given
    class MyModel(BaseModel):
        name: str = Field(..., description="Name of the person")
        profile_url: HttpUrl = Field(..., description="Profile URL")
        list_of_urls: list[HttpUrl] = Field(
            default_factory=list, description="List of URLs"
        )
        list_of_urls_or_none: list[HttpUrl] | None = Field(
            default=None, description="List of URLs or None"
        )

    from src.settings import Settings

    parser = OllamaExtractor(Settings())

    # when
    model = parser.create_response_model(MyModel)
    response = model(
        score=0.9,
        name="John Doe",
        profile_url="http://example.com/johndoe",
        list_of_urls=["http://example.com/url1", "http://example.com/url2"],
    )

    # then
    assert "profile_url" not in response.model_dump()
    assert "list_of_urls" not in response.model_dump()
    assert "list_of_urls_or_none" not in response.model_dump()
