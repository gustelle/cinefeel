from __future__ import annotations

from typing import Self

from loguru import logger
from pydantic import ConfigDict, Field, model_validator

from src.entities.base import Identifiable


class EntityComponent(Identifiable):
    """
    An object that can be used to compose other objects.
    """

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True)

    parent_uid: str = Field(
        ...,
        description="The parent to which this component belongs",
    )

    @model_validator(mode="after")
    def assign_uid(self) -> Self:
        """
        UID assignment is crucial for the entity merging process.
        It is important that the UID assignment is deterministic
        and consistent across different instances of the same component.
        """

        self.uid = f"{self.parent_uid}_{self.__class__.__name__.casefold()}"

        return self

    @staticmethod
    def override_or_complete(
        current_component: EntityComponent | None,
        current_score: float,
        component: EntityComponent,
        component_score: float,
    ) -> EntityComponent:
        """
        Override or complete the `EntityComponent` with the extraction result,
        proceeding to a fine grained assembly if needed.

        TODO:
        - test this method with various cases

        Args:
            current_component (EntityComponent | None): The current storable entity component.
            current_score (float): The score of the current storable entity.
            component (EntityComponent): The new component arrived from the extraction result.
            component_score (float): The score of the new component from the extraction result.

        Returns:
            EntityComponent: The updated or new storable entity.
        """

        if current_component is None:
            return component

        # exclude case where the candidate and storable do not relate to the same entity
        if current_component.uid != component.uid:
            logger.debug(
                f"EntityComponent '{current_component.uid}' does not match candidate UID {component.uid}"
            )
            return current_component

        # proceed to a json dump to compare the fields
        current_json = current_component.model_dump(
            mode="python",
            exclude_none=True,
        )
        candidate_json = component.model_dump(
            mode="python",
            exclude_none=True,
        )

        for key, value in candidate_json.items():

            if key not in current_json or current_json[key] is None:
                current_json[key] = value

            # if the key is already set and the value is a list,
            elif (
                current_json.get(key) is not None
                and isinstance(value, list)
                and component_score >= current_score
            ):
                # merge lists if both are lists
                try:
                    current_list: list = current_json.get(key, [])
                    current_list.extend(value)
                    current_json[key] = list(set(current_list))
                except TypeError:
                    # if the value is not a list, we just keep the current value
                    logger.warning(
                        f"Cannot merge list for key '{key}' into existing value '{current_json.get(key, [])}'"
                    )
            else:
                # nécessairement une valeur simple
                if component_score >= current_score:
                    current_json[key] = value

        # re-validate the storable with the updated json
        try:
            new_storable = current_component.__class__(
                **current_json,
            )

            return new_storable
        except Exception as e:
            # fallback to the original storable if validation fails

            logger.error(
                f"Validation error while updating '{current_component.__class__.__name__}' : {e}"
            )
            return current_component
