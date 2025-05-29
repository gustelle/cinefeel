from asyncio import Protocol


class ITaskExecutor(Protocol):
    """
    Interface for task executors.
    """

    def execute(self, *args, **kwargs) -> None:
        """
        Execute a given task.

        :param task: The task to be executed.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
