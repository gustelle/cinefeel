from typing import Protocol


class MLProcessor[T](Protocol):
    """
    Class to process ML operations
    """

    def process(self, *args, **kwargs) -> T | None:
        """
        Process the input and return an object of type T or None.

        """
        raise NotImplementedError("Subclasses should implement this method.")
