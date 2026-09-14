"""Exceptions raised by application storage services."""


class StorageError(RuntimeError):
    """Describe a failure while reading or writing application data."""

    def __init__(self, operation: str, path: str, cause: BaseException) -> None:
        """Initialize an error with operation, path, and original cause details."""
        self.operation = operation
        self.path = path
        self.cause = cause
        super().__init__(f"{operation} failed for {path}: {cause}")
