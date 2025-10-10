from asyncio import Protocol


class ITaskExecutor(Protocol):
    """
    Interface for task executors.
    """

    def execute_task(self, *args, return_results: bool = False, **kwargs) -> None:
        """
        Execute a given task.

        returns:
            None if return_results is False, otherwise returns the results of the task.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
