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
    score: float = Field(
        default=0.0,
        description="The score of the component, used to determine its relevance",
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

    def update(
        self,
        component: EntityComponent,
    ) -> Self:
        """
        update the current component with the values from the candidate component,
        in the same way a dict would be updated with another dict.

        Args:
            component (EntityComponent): The candidate component to merge with the current one.

        Returns:
            EntityComponent: The updated or new storable entity.
        """

        # exclude case where the candidate and storable do not relate to the same entity
        if self.uid != component.uid:
            logger.debug(
                f"EntityComponent '{self.uid}' does not match candidate UID {component.uid}"
            )
            return self

        # proceed to a json dump to compare the fields
        current_json = self.model_dump(
            mode="python",
            exclude_none=True,
        )
        candidate_json = component.model_dump(
            mode="python",
            exclude_none=True,
        )

        for key, value in candidate_json.items():

            if key in ["uid", "parent_uid", "score"]:
                # skip uid, parent_uid and score as they are not meant to be updated
                continue

            if key not in current_json or current_json[key] is None:
                current_json[key] = value

            # if the key is already set and the value is a list,
            elif current_json.get(key) is not None and isinstance(value, list):
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
                if component.score >= self.score:
                    current_json[key] = value

        # re-validate the storable with the updated json
        try:
            new_storable = self.__class__(
                **current_json,
            )

            return new_storable
        except Exception as e:
            # fallback to the original storable if validation fails
            logger.error(
                f"Validation error while updating '{self.__class__.__name__}' : {e}"
            )
            return self
