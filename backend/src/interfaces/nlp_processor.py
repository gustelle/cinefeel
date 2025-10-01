from abc import ABC, abstractmethod


class Processor[T](ABC):
    """
    Class to process ML operations
    """

    @abstractmethod
    def process(self, *args, **kwargs) -> T | None:
        """
        Process the input and return an object of type T or None.

        """
        raise NotImplementedError("Subclasses should implement this method.")
