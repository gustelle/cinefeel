from typing import Protocol, Sequence, Type

from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.content import Section, SectionTitle
from src.interfaces.extractor import IDataMiner


class ResolutionConfiguration:
    """
    Associates an extractor to a set of sections, and an expected type of entity to extract.
    """

    extractor: IDataMiner
    section_titles: Sequence[SectionTitle]
    extracted_type: Type[EntityComponent]
    resolve_as: Type[EntityComponent] | None = None

    def __init__(
        self,
        extractor: IDataMiner,
        section_titles: Sequence[SectionTitle],
        extracted_type: Type[EntityComponent],
        resolve_as: Type[EntityComponent] | None = None,
    ):
        """Initializes the resolution configuration.

        Args:
            extractor (IDataMiner): The data extractor to use for extracting information from the sections.
            section_titles (list[SectionTitle]): The titles of the sections to extract.
            extracted_type (Type[Storable]): The type of the entity to extract in the sections having the given titles.
            resolve_as (Type[Storable] | None): Optional type to resolve the extracted entity as.
                this is useful when you want to force resolution to a specific type.


        Example:
            ```python
            config = ResolutionConfiguration(
                extractor=my_extractor,
                section_titles=["Biography", "Career"],
                extracted_type=Biography,
            )

            config = ResolutionConfiguration(
                extractor=my_extractor,
                section_titles=["Visible Features"],
                extracted_type=PersonVisibleFeatures,
                resolve_as=PersonCharacteristics,
            )
            ```
        """
        self.extractor = extractor
        self.section_titles = section_titles
        self.extracted_type = extracted_type
        self.resolve_as = resolve_as


class IEntityResolver[T](Protocol):
    """
    Interface for an entity assembler that transforms content into a specific entity type.
    """

    config: ResolutionConfiguration

    def resolve(
        self,
        uid: str,
        base_info: Composable,
        sections: list[Section],
        *args,
        **kwargs,
    ) -> T:
        """
        Resolves a list of parts into an entity of type T.

        Args:
            uid (str): A unique identifier for the entity being resolved.
            parts (list[BaseModel]): A list of BaseModel instances that represent the content to be resolved.
                Each part should conform to the structure defined by the entity type T.
        """
        pass
