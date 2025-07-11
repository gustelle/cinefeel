from typing import Protocol


class IPipelineRunner(Protocol):
    """
    Interface for a pipeline that processes data.
    """

    def execute_pipeline(self, *args, **kwargs) -> None:
        """
        Run the pipeline with the given data.

        Args:
            data (dict): Input data to process.

        Returns:
            dict: Processed data.
        """
        pass
