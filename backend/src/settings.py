from pathlib import Path
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_yaml import parse_yaml_raw_as

from src.entities.content import TableOfContents


class SectionSettings(BaseSettings):
    """
    Settings related to section extraction.
    """

    model_config = SettingsConfigDict(
        env_prefix="sections_", env_file=(".env", ".env.prod"), extra="ignore"
    )

    max_children: int = Field(
        default=3,
        description="""
            The maximum number of children sections per section.
            If a section has more children than this value, the children will be truncated.
        """,
    )
    max_per_page: int = Field(
        default=5,
        description="""
            The maximum number of sections to extract from a page.
            If a page has more sections than this value, the sections will be truncated.
        """,
    )
    min_length: int = Field(
        default=500,
        description="""
            The minimum length of a section.
            If a section is shorter than this value, it will be ignored.
        """,
    )


class StorageSettings(BaseSettings):
    """
    Settings related to storage backends.
    """

    model_config = SettingsConfigDict(
        env_prefix="storage_", env_file=(".env", ".env.prod"), extra="ignore"
    )

    local_directory: str = Field(
        default=Path("./data").as_posix(),
        description="""
        The path (relative or absolute) to the dir where the scraped data will be saved.
        
        NB: this field is not declared as `Path` because we need it to be serializable by Prefect.
        """,
    )

    graphdb_uri: str | None = Field(
        default="bolt://localhost:7687/memgraph",
        description="""
            The URI of the database used to store the graph data.
            
            NB: this field is not declared as `AnyUrl` because we need it to be serializable by Prefect.
        """,
    )

    redis_dsn: str = Field(
        default="redis://localhost:6379/0",
        description="""
            used for storing html and JSON contents temporarily, before processing them into the Graph DB.
            NB: only the /0 database is supported because we are using RedisSearch module which does not support logical DBs.
            @see https://stackoverflow.com/questions/72116930/redisearch-cannot-create-index-on-db-0
            
            NB: this field is not declared as `RedisDsn` because we need it to be serializable by Prefect.
        """,
    )


class StatsSettings(BaseSettings):
    """
    Settings related to statistics backends.
    """

    model_config = SettingsConfigDict(
        env_prefix="stats_", env_file=(".env", ".env.prod"), extra="ignore"
    )

    redis_dsn: str = Field(
        default="redis://localhost:6379/2",
        description="""
            used for storing statistics about the scraping and extraction processes.
            
            NB: this field is not declared as `RedisDsn` because we need it to be serializable by Prefect.
        """,
    )


class MLSettings(BaseSettings):
    """
    Settings related to content summarization.
    """

    model_config = SettingsConfigDict(
        env_prefix="ml_", env_file=(".env", ".env.prod"), extra="ignore"
    )

    summary_model: str = Field(
        default="paraphrase-MiniLM-L6-v2",
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

    transformer_model_backend: str = Field(
        default="openvino",
        pattern="^(torch|onnx|openvino)$",
        description="""
            can't use GPU on macOS with docker, 
            so using OpenVINO for better performance on CPU
            may be a good deal.
        """,
        examples=["torch", "onnx", "openvino"],
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


class PrefectSettings(BaseSettings):
    """
    Settings related to Prefect orchestration.
    """

    model_config = SettingsConfigDict(
        env_prefix="prefect_", env_file=(".env", ".env.prod"), extra="ignore"
    )

    flows_concurrency_limit: int = Field(
        default=2,
        description="The maximum number of concurrent flows",
    )

    task_timeout: int = Field(
        default=60 * 30,  # 30 minutes
        description="The timeout for prefect tasks in seconds",
    )
    tasks_concurrency_limit: int = Field(
        default=10,
        description="The maximum number of concurrent prefect tasks",
    )
    cache_disabled: bool = Field(
        default=False,
        description="If True, disables the prefect task cache",
    )


class ScrapingSettings(BaseSettings):
    """
    Settings related to scraping.
    """

    model_config = SettingsConfigDict(
        env_prefix="scraping_",
        env_file=(".env", ".env.prod"),
        extra="ignore",
    )

    cache_expire_after: int = Field(
        default=60 * 60 * 24,
        description="The expiration time of the cache in seconds",
    )
    start_pages: list[TableOfContents] | None = Field(
        None,
        description="Will be set through the start pages config file",
    )

    config_file: str | None = Field(
        default="./start-pages-dev.yml",
        description="""
            The path to the YAML configuration file for the start pages,
            must be provided in the .env file as `START_PAGES_CONFIG`.
        """,
    )

    max_concurrency: int = Field(
        default=3,
        description="The maximum number of concurrent connections to download pages",
    )
    request_timeout: int = Field(
        default=10,
        description="The timeout for each request in seconds",
    )
    mediawiki_api_key: str = Field(
        default="",
        description="""
            The API key for the MediaWiki API;
            see https://api.wikimedia.org/wiki/Special:AppManagement
        """,
    )
    mediawiki_base_url: str = Field(
        default="https://api.wikimedia.org/core/v1/wikipedia/fr",
        description="The base URL of the Wikipedia API",
    )
    mediawiki_user_agent: str = Field(
        default="Cinefeel",
        description="The user agent to use for the Wikipedia API",
    )

    @model_validator(mode="after")
    def on_after_init(self) -> Self:

        if not self.config_file or not Path(self.config_file).exists():
            raise ValueError(
                f"start_pages_config is not set or the file does not exist: {self.config_file}"
            )

        with open(self.config_file, "r") as f:
            list_of_tocs = parse_yaml_raw_as(list[TableOfContents], f.read())
            self.start_pages = list_of_tocs

        return self


class SearchSettings(BaseSettings):
    """
    Settings related to search engine.
    """

    model_config = SettingsConfigDict(
        env_prefix="search_",
        env_file=(".env", ".env.prod"),
        extra="ignore",
    )

    base_url: str | None = Field(
        default="http://localhost:7700",
        description="The base URL of the MeiliSearch API",
    )
    api_key: str = Field(
        default="cinefeel",
        description="The API key for the MeiliSearch API",
    )
    movies_index_name: str = Field(
        default="movies",
    )
    persons_index_name: str = Field(
        default="persons",
    )


class AppSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod"),
        extra="ignore",
    )
    search_settings: SearchSettings = Field(
        default_factory=SearchSettings,
    )
    storage_settings: StorageSettings = Field(
        default_factory=StorageSettings,
    )
    prefect_settings: PrefectSettings = Field(
        default_factory=PrefectSettings,
    )
    ml_settings: MLSettings = Field(
        default_factory=MLSettings,
    )
    section_settings: SectionSettings = Field(
        default_factory=SectionSettings,
    )
    stats_settings: StatsSettings = Field(
        default_factory=StatsSettings,
    )
    scraping_settings: ScrapingSettings = Field(
        default_factory=ScrapingSettings,
    )
