class BaseAppException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DocumentProcessingError(BaseAppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=422, details=details)

class GraphDatabaseError(BaseAppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=500, details=details)

class ExternalAPIError(BaseAppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=502, details=details)

class GraphRAGRetrievalError(BaseAppException):
    """Raised when graph retrieval yields zero relevant results."""
    def __init__(self, message: str = "No relevant information found in the knowledge graph.", details: dict = None):
        super().__init__(message=message, status_code=404, details=details)

class QueryTimeoutError(BaseAppException):
    """Raised when the total GraphRAG pipeline exceeds the configured timeout."""
    def __init__(self, message: str = "Query processing exceeded the maximum allowed time.", details: dict = None):
        super().__init__(message=message, status_code=504, details=details)
