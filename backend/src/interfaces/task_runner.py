class ITaskRunner:
    """
    Interface for a task runner.
    """

    def is_ready(self) -> bool:
        """
        Check if the task runner is ready.

        :return: True if the task runner is ready, False otherwise.
        """
        raise NotImplementedError("TaskRunner.is_ready() must be implemented.")

    def submit(self, *args, **kwargs) -> None:
        """
        Run the given task.

        :param task: The task to run.
        """
        raise NotImplementedError("TaskRunner.run() must be implemented.")
