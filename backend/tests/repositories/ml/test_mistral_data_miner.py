from src.entities.composable import Composable
from src.entities.ml import ExtractionResult
from src.entities.person import Biography
from src.repositories.ml.mistral_data_miner import MistralDataMiner
from src.settings import Settings

from .stub.stub_llm import StubMistral


def test_parent_uid_is_attached_to_entity(mocker, test_settings: Settings):

    # given
    # the uid will be generated from the title
    base_info = Composable(
        title="Test Title",
        permalink="http://example.com/test",
    )

    mock_llm_response = (
        '{"score": 0.95, "parent_uid": "test_uid", "full_name": "John Doe"}'
    )

    # suppose Mistral chat responds with a JSON string
    mocker.patch(
        "src.repositories.ml.mistral_data_miner.Mistral",
        return_value=StubMistral(mock_llm_response),
    )

    parser = MistralDataMiner(test_settings)
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
