from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=(".env", ".env.prod")
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
    meili_index_name: str = Field(
        default="films",
        description="The name of the MeiliSearch index",
    )
