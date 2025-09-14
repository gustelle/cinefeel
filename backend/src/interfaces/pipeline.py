from typing import Protocol


class IPipelineRunner(Protocol):
    """
    Interface for a pipeline that processes data.

    A pipeline typically consists of multiple stages that transform input data into output data.
    Each stage can perform operations such as data extraction, transformation, validation, and loading.

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
