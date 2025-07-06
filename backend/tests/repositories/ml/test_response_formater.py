from typing import Annotated

import pytest
from pydantic import BaseModel, Field, HttpUrl, StringConstraints

from src.repositories.ml.response_formater import create_response_model


def test_create_response_model():

    # given
    class MyModel(BaseModel):
        height: int = Field(..., description="Height in centimeters")

    # when
    response = create_response_model(MyModel)(score=0.9, height=180)

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

    # when
    model = create_response_model(MyModel)
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


def test_create_response_model_for_non_pydantic_entity():

    # given
    # a type which is not a Pydantic model
    ParentTrade = Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=0,
        ),
    ]  # may be empty for some sections

    # when
    with pytest.raises(TypeError):
        create_response_model(ParentTrade)


@pytest.mark.skip(reason="This test is not relevant for the current implementation")
def test_uid_is_excluded_from_response_model():

    # given
    class MyModel(BaseModel):
        uid: str = Field(..., description="Unique identifier")
        name: str = Field(..., description="Name of the person")

    # when
    model = create_response_model(MyModel)
    response = model(score=0.9, uid="12345", name="John Doe")

    # then
    assert "uid" not in response.model_dump()
    assert response.name == "John Doe"
    assert response.score == 0.9
