from pathlib import Path
from typing import Self

from pydantic import AnyUrl, Field, HttpUrl, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_yaml import parse_yaml_raw_as

from src.entities.content import TableOfContents


class Settings(BaseSettings):

    # TODO:
    # - refactor the settings, merging mistral_xxx and ollama_xxx into LLSettings
    # - refactor the settings, merging mediawiki_base_url and mediawiki_api_key into MediaWikiSettings
    # - refactor the settings, merging search_xxx into SearchSettings
    # - refactor the settings, merging graph_db_xxx, meili and redis_xxx into StorageSettings

    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=(".env", ".env.prod")
    )

    scraping_cache_expire_after: int = Field(
        default=60 * 60 * 24,
        description="The expiration time of the cache in seconds",
    )
    scraping_start_pages: list[TableOfContents] | None = Field(
        None,
        description="Will be set through the start pages config file",
    )

    scraping_config_file: Path | None = Field(
        ...,
        description="""
            The path to the YAML configuration file for the start pages,
            must be provided in the .env file as `START_PAGES_CONFIG`.
        """,
    )

    scraping_max_concurrency: int = Field(
        default=10,
        description="The maximum number of concurrent connections to download pages",
    )

    mediawiki_api_key: str = Field(
        default="",
        description="The API key for the MediaWiki API",
    )
    mediawiki_base_url: str = Field(
        default="https://api.wikimedia.org/core/v1/wikipedia/fr",
        description="The base URL of the Wikipedia API",
    )
    mediawiki_user_agent: str = Field(
        default="Cinefeel",
        description="The user agent to use for the Wikipedia API",
    )
    mediawiki_user_agent: str = Field(
        default="Cinefeel",
        description="The user agent to use for the Wikipedia API",
    )

    search_base_url: HttpUrl | None = Field(
        default="http://localhost:7700",
        description="The base URL of the MeiliSearch API",
    )
    search_api_key: str = Field(
        default="cinefeel",
        description="The API key for the MeiliSearch API",
    )
    search_movies_index_name: str = Field(
        default="movies",
    )
    search_persons_index_name: str = Field(
        default="persons",
    )

    local_storage_directory: Path = Field(
        default=Path("./data"),
        description="The path (relative or absolute) to the dir where the scraped data will be saved",
    )

    mistral_llm_model: str = Field(
        default="mistral-medium-latest",
    )

    mistral_api_key: SecretStr = Field(
        default="",
        description="The API key for the Mistral API",
    )

    ollama_llm_model: str = Field(
        default="llama3-chatqa:latest",
        description="The name of the LLM model to use for text processing.",
    )

    ollama_vision_model: str = Field(
        default="llava:7b",
        description="""
            The name of the vision model to use for image processing.
            """,
    )

    similarity_model: str = Field(
        default="sentence-transformers/nli-mpnet-base-v2",
        description="""
            The name of the BERT model to use for similarity search
        """,
    )

    similarity_min_score: float = Field(
        default=0.7,
        ge=0,
        le=1,
        description="""
            The threshold for the similarity score.
            If the score is below this value, the result will be considered as not found.
            Be careful, the threshold is really dependent on the model used.
        """,
    )

    summary_model: str = Field(
        default="facebook/bart-large-cnn",
        description="""
            The model to use for summarizing contents.
        """,
    )

    summary_max_length: int = Field(
        default=512,
        description="""
            The maximum length of the summary generated from a section content.
            If the content is longer than this value, it will be truncated.
            Too short summaries would lead to poor results.
        """,
    )

    summary_min_length: int = Field(
        default=256,
        description="""
            The minimum length of the summary generated from a section content.
            If the content is shorter than this value, it will be ignored.
            Too short summaries would lead to poor results.
        """,
    )

    prefect_task_timeout: int = Field(
        default=60 * 30,  # 30 minutes
        description="The timeout for prefect tasks in seconds",
    )
    prefect_concurrency_limit: int = Field(
        default=10,
        description="The maximum number of concurrent prefect tasks",
    )

    # section params
    sections_max_children: int = Field(
        default=3,
        description="""
            The maximum number of children sections per section.
            If a section has more children than this value, the children will be truncated.
        """,
    )
    sections_max_per_page: int = Field(
        default=5,
        description="""
            The maximum number of sections to extract from a page.
            If a page has more sections than this value, the sections will be truncated.
        """,
    )
    sections_min_length: int = Field(
        default=500,
        description="""
            The minimum length of a section.
            If a section is shorter than this value, it will be ignored.
        """,
    )

    graph_db_uri: AnyUrl | None = Field(
        ...,
        description="""
            The URI of the database used to store the graph data.
        """,
    )

    redis_storage_dsn: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="""
            used for storing html and JSON contents temporarily, before processing them into the Graph DB.
            NB: only the /0 database is supported because we are using RedisSearch module which does not support logical DBs.
            @see https://stackoverflow.com/questions/72116930/redisearch-cannot-create-index-on-db-0
        """,
    )

    @model_validator(mode="after")
    def on_after_init(self) -> Self:

        if not self.scraping_config_file or not self.scraping_config_file.exists():
            raise ValueError(
                f"start_pages_config is not set or the file does not exist: {self.scraping_config_file}"
            )

        with open(self.scraping_config_file, "r") as f:
            list_of_tocs = parse_yaml_raw_as(list[TableOfContents], f.read())
            self.scraping_start_pages = list_of_tocs

        return self
