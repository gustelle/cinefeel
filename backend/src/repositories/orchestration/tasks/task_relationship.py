from logging import Logger

from prefect import task
from prefect.concurrency.sync import rate_limit
from prefect.events import emit_event

from src.entities.composable import Composable
from src.entities.movie import Movie
from src.entities.relationship import (
    LooseRelationship,
    PeopleRelationshipType,
    RelationshipType,
    StrongRelationship,
)
from src.exceptions import RetrievalError
from src.interfaces.http_client import IHttpClient
from src.interfaces.storage import IRelationshipHandler
from src.repositories.wikipedia import get_page_id, get_permalink

from .logger import get_task_logger


def connect_by_name(
    entity: Composable,
    name: str,
    relation: RelationshipType,
    storage: IRelationshipHandler,
    http_client: IHttpClient,
) -> None:
    """Connects an entity to another entity.

    Several cases are handled:
    1. If the related entity identified by its `name` exists on Wikipedia and in the storage, a StrongRelationship is created.
    2. If the related entity exists on Wikipedia but not in the storage, an event is emitted to extract the entity later
         (e.g., via another task).
    3. If the related entity does not exist on Wikipedia, a LooseRelationship is created.

    Args:
        entity (Composable): The source entity.
        name (str): The name of the related entity.
        relation (RelationshipType): The type of relationship.
        storage (IRelationshipHandler): The storage handler for relationships.
        http_client (IHttpClient): The HTTP client for making requests.

    Returns:
        Relationship | None: The created relationship or None if unsuccessful.
    """
    logger: Logger = get_task_logger()
    try:
        rate_limit("api-rate-limiting", occupy=1)
        permalink = get_permalink(name=name, http_client=http_client)

        # query the storage for the entity by its permalink
        results = storage.query(
            permalink=permalink,
            limit=1,
        )

        if results is not None and len(results) > 0:
            storage.add_relationship(
                relationship=StrongRelationship(
                    from_entity=entity,
                    to_entity=results[0],
                    relation_type=relation,
                )
            )
        else:
            page_id = get_page_id(permalink=permalink)
            emit_event(
                event="extract.entity",
                resource={"prefect.resource.id": page_id},
                payload={"entity_type": storage.entity_type.__name__},
            )

    except RetrievalError as e:
        if e.status_code == 404:
            # case 1:
            # the entity does not exist on Wikipedia
            storage.add_relationship(
                relationship=LooseRelationship(
                    from_entity=entity,
                    to_title=name,
                    relation_type=relation,
                )
            )
        else:
            # case 2:
            logger.error(f"RetrievalError while connecting entity: {e}")
            # re-raise the error or handle it as needed
            raise


@task(
    task_run_name="execute_task-{entity.uid}",
)
def execute_task(
    entity: Composable,
    output_storage: IRelationshipHandler,
    http_client: IHttpClient,
) -> Composable:
    """
    discovers relationships for a given entity and stores them in the graph database.
    TODO:
    - rename to discover_relationships_task
    - rename param output_storage to relationship_storage

    Args:
        entity (Composable): The entity to analyze.
        output_storage (IRelationshipHandler): The storage handler to use for storing the relationships.
        http_client (IHttpClient): The HTTP client for making requests.

    """

    if isinstance(entity, Movie):

        if (
            entity.specifications is not None
            and entity.specifications.directed_by is not None
        ):

            for name in entity.specifications.directed_by:

                connect_by_name(
                    entity=entity,
                    name=name,
                    relation=PeopleRelationshipType.DIRECTED_BY,
                    storage=output_storage,
                    http_client=http_client,
                )

        # retrieve the persons that wrote the script of the film
        if (
            entity.specifications is not None
            and entity.specifications.written_by is not None
        ):

            for name in entity.specifications.written_by:

                connect_by_name(
                    entity=entity,
                    name=name,
                    relation=PeopleRelationshipType.WRITTEN_BY,
                    storage=output_storage,
                    http_client=http_client,
                )

        # retrieve the persons that composed the music of the film
        if (
            entity.specifications is not None
            and entity.specifications.music_by is not None
        ):

            for name in entity.specifications.music_by:

                connect_by_name(
                    entity=entity,
                    name=name,
                    relation=PeopleRelationshipType.COMPOSED_BY,
                    storage=output_storage,
                    http_client=http_client,
                )

        # retrieve the persons that influenced the film
        if entity.influences is not None and len(entity.influences) > 0:
            for influence in entity.influences:
                if influence.persons is not None and len(influence.persons) > 0:
                    for name in influence.persons:

                        connect_by_name(
                            entity=entity,
                            name=name,
                            relation=PeopleRelationshipType.INFLUENCED_BY,
                            storage=output_storage,
                            http_client=http_client,
                        )

        # retrieve the persons that did the special effects of the film
        if (
            entity.specifications is not None
            and entity.specifications.special_effects_by is not None
        ):

            for name in entity.specifications.special_effects_by:

                connect_by_name(
                    entity=entity,
                    name=name,
                    relation=PeopleRelationshipType.SPECIAL_EFFECTS_BY,
                    storage=output_storage,
                    http_client=http_client,
                )

    return entity
