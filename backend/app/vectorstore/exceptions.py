class VectorStoreError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CollectionError(VectorStoreError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)


class IndexError(VectorStoreError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)


class ConnectionError(VectorStoreError):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message, status_code)
