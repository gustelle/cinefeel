from typing import Any
from uuid import UUID

from prefect.results import ResultStore, get_or_create_default_task_scheduling_storage
from prefect.task_worker import read_parameters
from prefect.tasks import Task


async def get_background_task_run_parameters(
    task: Task[Any, Any], parameters_id: UUID
) -> Any:
    store = await ResultStore(
        result_storage=await get_or_create_default_task_scheduling_storage()
    ).update_for_task(task)
    return await read_parameters(store, parameters_id)
