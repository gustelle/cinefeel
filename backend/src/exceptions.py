class _BaseError(Exception):
    """Base class for all custom exceptions in the application."""

    reason: str

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class RetrievalError(_BaseError):
    """Exception raised for errors during data retrieval operations."""

    status_code: int

    def __init__(self, reason: str, status_code: int):
        self.status_code = status_code
        super().__init__(reason)


class HttpError(RetrievalError):
    pass


class ParsingError(_BaseError):
    pass


class StorageError(_BaseError):
    pass


class SummaryError(_BaseError):
    pass


class RelationshipError(_BaseError):
    pass


class SimilaritySearchError(RetrievalError):

    pass
