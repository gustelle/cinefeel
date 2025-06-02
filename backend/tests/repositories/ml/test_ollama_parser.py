from src.entities.person import PersonCharacteristics


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

    response = '{"handicaps":["sourd", "aveugle"]}'

    mocker.patch(
        "src.repositories.ml.ollama_parser.ollama.chat",
        return_value=MockResponse(MockMessage(response)),
    )

    from src.repositories.ml.ollama_parser import OllamaExtractor
    from src.settings import Settings

    parser = OllamaExtractor(Settings())
    content = "This is a test content for Ollama."
    entity_type = PersonCharacteristics

    # when
    result = parser.extract_entity(content, entity_type)

    # then
    assert isinstance(result, PersonCharacteristics)
    assert result.disabilities == ["sourd", "aveugle"]
