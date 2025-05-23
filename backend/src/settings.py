from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WikiTOCPageConfig(BaseModel):
    """Configuration for a Wikipedia Table-of-content (TOC) page.

    A table of content page is a page that contains a list of links to other pages.
    For example, the page "Liste de films français sortis en 1907" contains a list of links to
    all the films released in 1907.
    """

    page_id: str = Field(
        default="",
        description="The ID of the Wikipedia page",
        examples=["Film_Title", "Liste_de_films_français_sortis_en_1907"],
    )

    toc_css_selector: str = Field(
        default=".wikitable td:nth-child(1)",
        description="""
            The CSS selector to use to extract the links from the table of contents.
        """,
        examples=[".wikitable td:nth-child(1)"],
    )

    toc_content_type: Literal["film", "person"] = Field(
        ...,
        description="""
            The type of content to extract from the TOC page.
            Can be either "film" or "person".
            Example: 
            - "film" for a page containing a list of films,
            - "person" for a page containing a list of people.
        """,
        examples=["film", "person"],
    )


_default_film_tocs = [
    WikiTOCPageConfig(
        page_id=f"Liste_de_films_français_sortis_en_{year}",
        toc_css_selector=".wikitable td:nth-child(1)",
        toc_content_type="film",
    )
    for year in range(1907, 1908)
]

_default_person_tocs = [
    WikiTOCPageConfig(
        page_id=f"Liste_de_films_français_sortis_en_{year}",
        toc_css_selector=".wikitable td:nth-child(2)",
        toc_content_type="person",
    )
    for year in range(1907, 1908)
]
_default_tocs = _default_film_tocs + _default_person_tocs


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=(".env", ".env.prod")
    )

    crawler_use_cache: bool = Field(
        default=True,
        description="Whether to use the cache for the Wikipedia API",
    )
    crawler_cache_expire_after: int = Field(
        default=60 * 60 * 24,
        description="The expiration time of the cache in seconds",
    )

    mediawiki_api_key: str
    mediawiki_base_url: str = Field(
        default="https://api.wikimedia.org/core/v1/wikipedia/fr",
        description="The base URL of the Wikipedia API",
    )
    mediawiki_user_agent: str = Field(
        default="Cinefeel",
        description="The user agent to use for the Wikipedia API",
    )
    mediawiki_start_pages: list[WikiTOCPageConfig] = Field(
        default=_default_tocs,
    )

    scraper_max_concurrent_connections: int = Field(
        default=10,
        description="The maximum number of concurrent connections to the Wikipedia API",
    )
    scraper_user_agent: str = Field(
        default="Cinefeel",
        description="The user agent to use for the Wikipedia API",
    )

    meili_base_url: str = Field(
        default="http://localhost:7700",
        description="The base URL of the MeiliSearch API",
    )
    meili_api_key: str = Field(
        default="cinefeel",
        description="The API key for the MeiliSearch API",
    )
    meili_films_index_name: str = Field(
        default="films",
    )
    meili_persons_index_name: str = Field(
        default="persons",
    )

    persistence_directory: Path = Field(
        default=Path("./data"),
        description="The path (relative or absolute) to the dir where the scraped data will be saved",
    )

    llm_model: str = Field(
        default="mistral:latest",
        description="The name of the LLM model to use",
    )

    llm_question: str = Field(
        default="Donne-moi des informations sur le film, réponds en français et de manière concise, sans faire de phrases. Si tu ne trouves pas d'informations, n'invente pas.",
        examples=[
            "Donne-moi des informations sur le film",
            "Quelles sont les informations sur le film ?",
            "Peux-tu me parler du film ?",
        ],
        description="The question to ask the LLM model to get information about the film",
    )

    bert_model: str = Field(
        default="Lajavaness/sentence-camembert-base",
        description="""
            The name of the BERT model to use for similarity search
            when analyzing the content of a HTML page.
            this model is used to find the most similar section corresponding to a query.
            For example, the query "fiche technique" will be used to find the section
            containing the technical specifications of a film.
        """,
    )

    bert_similarity_threshold: float = Field(
        default=0.9,
        description="""
            The threshold for the BERT similarity score.
            If the score is below this value, the result will be considered as not found.
        """,
    )
