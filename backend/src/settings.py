from pathlib import Path

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
    mediawiki_start_pages: list[str] = Field(
        default=[
            "Liste_de_films_français_sortis_en_1907",
            "Liste_de_films_français_sortis_en_1908",
            "Liste_de_films_français_sortis_en_1909",
            "Liste_de_films_français_sortis_en_1910",
            "Liste_de_films_français_sortis_en_1911",
            "Liste_de_films_français_sortis_en_1912",
            "Liste_de_films_français_sortis_en_1913",
            "Liste_de_films_français_sortis_en_1914",
            "Liste_de_films_français_sortis_en_1915",
            "Liste_de_films_français_sortis_en_1916",
            "Liste_de_films_français_sortis_en_1917",
            "Liste_de_films_français_sortis_en_1918",
            "Liste_de_films_français_sortis_en_1919",
            "Liste_de_films_français_sortis_en_1920",
            # "Liste_de_films_français_sortis_en_1921",
            # "Liste_de_films_français_sortis_en_1922",
            # "Liste_de_films_français_sortis_en_1923",
            # "Liste_de_films_français_sortis_en_1924",
            # "Liste_de_films_français_sortis_en_1925",
            # "Liste_de_films_français_sortis_en_1926",
            # "Liste_de_films_français_sortis_en_1927",
            # "Liste_de_films_français_sortis_en_1928",
            # "Liste_de_films_français_sortis_en_1929",
            # "Liste_de_films_français_sortis_en_1930",
            # "Liste_de_films_français_sortis_en_1931",
            # "Liste_de_films_français_sortis_en_1932",
            # "Liste_de_films_français_sortis_en_1933",
            # "Liste_de_films_français_sortis_en_1934",
            # "Liste_de_films_français_sortis_en_1935",
            # "Liste_de_films_français_sortis_en_1936",
            # "Liste_de_films_français_sortis_en_1937",
            # "Liste_de_films_français_sortis_en_1938",
            # "Liste_de_films_français_sortis_en_1939",
            # "Liste_de_films_français_sortis_en_1940",
            # "Liste_de_films_français_sortis_en_1941",
            # "Liste_de_films_français_sortis_en_1942",
            # "Liste_de_films_français_sortis_en_1943",
            # "Liste_de_films_français_sortis_en_1944",
            # "Liste_de_films_français_sortis_en_1945",
            # "Liste_de_films_français_sortis_en_1946",
            # "Liste_de_films_français_sortis_en_1947",
            # "Liste_de_films_français_sortis_en_1948",
            # "Liste_de_films_français_sortis_en_1949",
            # "Liste_de_films_français_sortis_en_1950",
            # "Liste_de_films_français_sortis_en_1951",
            # "Liste_de_films_français_sortis_en_1952",
            # "Liste_de_films_français_sortis_en_1953",
            # "Liste_de_films_français_sortis_en_1954",
            # "Liste_de_films_français_sortis_en_1955",
            # "Liste_de_films_français_sortis_en_1956",
            # "Liste_de_films_français_sortis_en_1957",
            # "Liste_de_films_français_sortis_en_1958",
            # "Liste_de_films_français_sortis_en_1959",
            # "Liste_de_films_français_sortis_en_1960",
            # "Liste_de_films_français_sortis_en_1961",
            # "Liste_de_films_français_sortis_en_1962",
            # "Liste_de_films_français_sortis_en_1963",
            # "Liste_de_films_français_sortis_en_1964",
            # "Liste_de_films_français_sortis_en_1965",
            # "Liste_de_films_français_sortis_en_1966",
            # "Liste_de_films_français_sortis_en_1967",
            # "Liste_de_films_français_sortis_en_1968",
            # "Liste_de_films_français_sortis_en_1969",
            # "Liste_de_films_français_sortis_en_1970",
            # "Liste_de_films_français_sortis_en_1971",
            # "Liste_de_films_français_sortis_en_1972",
            # "Liste_de_films_français_sortis_en_1973",
            # "Liste_de_films_français_sortis_en_1974",
            # "Liste_de_films_français_sortis_en_1975",
            # "Liste_de_films_français_sortis_en_1976",
            # "Liste_de_films_français_sortis_en_1977",
            # "Liste_de_films_français_sortis_en_1978",
            # "Liste_de_films_français_sortis_en_1979",
            # "Liste_de_films_français_sortis_en_1980",
            # "Liste_de_films_français_sortis_en_1981",
            # "Liste_de_films_français_sortis_en_1982",
            # "Liste_de_films_français_sortis_en_1983",
            # "Liste_de_films_français_sortis_en_1984",
            # "Liste_de_films_français_sortis_en_1985",
            # "Liste_de_films_français_sortis_en_1986",
            # "Liste_de_films_français_sortis_en_1987",
            # "Liste_de_films_français_sortis_en_1988",
            # "Liste_de_films_français_sortis_en_1989",
            # "Liste_de_films_français_sortis_en_1990",
            # "Liste_de_films_français_sortis_en_1991",
            # "Liste_de_films_français_sortis_en_1992",
            # "Liste_de_films_français_sortis_en_1993",
            # "Liste_de_films_français_sortis_en_1994",
            # "Liste_de_films_français_sortis_en_1995",
            # "Liste_de_films_français_sortis_en_1996",
            # "Liste_de_films_français_sortis_en_1997",
            # "Liste_de_films_français_sortis_en_1998",
            # "Liste_de_films_français_sortis_en_1999",
            # "Liste_de_films_français_sortis_en_2000",
            # "Liste_de_films_français_sortis_en_2001",
            # "Liste_de_films_français_sortis_en_2002",
            # "Liste_de_films_français_sortis_en_2003",
            # "Liste_de_films_français_sortis_en_2004",
            # "Liste_de_films_français_sortis_en_2005",
            # "Liste_de_films_français_sortis_en_2006",
            # "Liste_de_films_français_sortis_en_2007",
            # "Liste_de_films_français_sortis_en_2008",
            # "Liste_de_films_français_sortis_en_2009",
            # "Liste_de_films_français_sortis_en_2010",
            # "Liste_de_films_français_sortis_en_2011",
            # "Liste_de_films_français_sortis_en_2012",
            # "Liste_de_films_français_sortis_en_2013",
            # "Liste_de_films_français_sortis_en_2014",
            # "Liste_de_films_français_sortis_en_2015",
            # "Liste_de_films_français_sortis_en_2016",
            # "Liste_de_films_français_sortis_en_2017",
            # "Liste_de_films_français_sortis_en_2018",
            # "Liste_de_films_français_sortis_en_2019",
            # "Liste_de_films_français_sortis_en_2020",
            # "Liste_de_films_français_sortis_en_2021",
            # "Liste_de_films_français_sortis_en_2022",
            # "Liste_de_films_français_sortis_en_2023",
            # "Liste_de_films_français_sortis_en_2024",
            # "Liste_de_films_français_sortis_en_2025",
        ],
        description="The list of Wikipedia pages to scrape",
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
