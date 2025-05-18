from typing import Awaitable, Sequence

from src.interfaces.task_runner import ITaskRunner


class DramatiqRunner(ITaskRunner):
    """
    A class to run Dask tasks in non-blocking mode.
    """

    def is_ready(self) -> bool:
        """
        Check if the Dask client is ready.
        :return: True if the Dask client is ready, False otherwise.
        """
        return True

    async def submit(self, coro: Awaitable, *args, **kwargs):
        """
        Run a function with Dask.
        """

        ...

    async def gather(self, *tasks) -> Sequence:
        """
        Gather the results of the given tasks by running them with Dask in non-blocking mode.
        :param coros: The tasks to gather.

        Errors are skipped and not raised, thus the results may contain None values.

        Returns:
            The results of the tasks.
        """

        ...
