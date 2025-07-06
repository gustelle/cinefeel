# given
import pytest

from src.entities.composable import Composable
from src.entities.content import Media
from src.entities.person import PersonVisibleFeatures
from src.repositories.ml.ollama_person_visualizer import PersonVisualAnalysis
from src.settings import Settings


@pytest.mark.skip(reason="Requires Ollama server to be running")
def test_visual_analysis():
    # given

    settings = Settings()
    base_info = Composable(
        uid="test_uid",
        title="Test Title",
        permalink="http://example.com/test",
    )

    content = "This is a test content for Ollama."
    src = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Quentin_Tarantino_by_Gage_Skidmore.jpg/500px-Quentin_Tarantino_by_Gage_Skidmore.jpg"
    media = [Media(uid="test_media_uid", src=src, media_type="image")]
    entity_type = PersonVisibleFeatures

    extractor = PersonVisualAnalysis(settings)

    # when
    result = extractor.extract_entity(
        content=content,
        media=media,
        entity_type=entity_type,
        base_info=base_info,
    )

    # then
    print(result.model_dump_json(indent=2))
