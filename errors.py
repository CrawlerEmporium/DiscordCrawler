class CrawlerException(Exception):
    """A base exception class."""

    def __init__(self, msg):
        super().__init__(msg)


class InvalidArgument(CrawlerException):
    """Raised when an argument is invalid."""
    pass


class EvaluationError(CrawlerException):
    """Raised when a cvar evaluation causes an error."""

    def __init__(self, original, expression=None):
        super().__init__(f"Error evaluating expression: {original}")
        self.original = original
        self.expression = expression


class SelectionException(CrawlerException):
    """A base exception for message awaiting exceptions to stem from."""
    pass
