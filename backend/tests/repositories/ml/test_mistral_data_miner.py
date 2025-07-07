from src.entities.composable import Composable
from src.entities.ml import ExtractionResult
from src.entities.person import Biography
from src.repositories.ml.mistral_data_miner import MistralDataMiner
from src.settings import Settings


def test_parent_uid_is_attached_to_entity(mocker):
    # given
    base_info = Composable(
        title="Test Title",
        permalink="http://example.com/test",
    )

    class MockMessage:
        content: str

        def __init__(self, content):
            self.content = content

    class MockChoice:
        message: MockMessage

        def __init__(self, message):
            self.message = message

    class MockChat:

        message: str
        choices: list[MockChoice]

        def __init__(self, message):
            self.choices = [MockChoice(MockMessage(message))]

        def parse(self, *args, **kwargs):
            return self

    class MockResponse:

        message: str

        def __init__(self, message):
            self.message = message

        @property
        def chat(self):
            return MockChat(self.message)

    mock_llm_response = (
        '{"score": 0.95, "parent_uid": "test_uid", "nom_complet": "John Doe"}'
    )

    # suppose Mistral chat responds with a JSON string
    mocker.patch(
        "src.repositories.ml.mistral_data_miner.Mistral",
        return_value=MockResponse(mock_llm_response),
    )

    parser = MistralDataMiner(Settings())
    entity_type = Biography

    # when
    result = parser.extract_entity(
        "",
        [],
        entity_type,
        base_info,
    )

    # then
    assert isinstance(result, ExtractionResult)
    assert isinstance(result.entity, Biography)
    assert result.entity.parent_uid == base_info.uid
    assert result.score == 0.95
