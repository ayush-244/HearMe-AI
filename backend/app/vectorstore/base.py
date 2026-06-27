from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class VectorStore(ABC):
    @abstractmethod
    def initialize(self) -> None:
        ...

    @abstractmethod
    def create_collection(self) -> None:
        ...

    @abstractmethod
    def delete_collection(self) -> None:
        ...

    @abstractmethod
    def collection_exists(self) -> bool:
        ...

    @abstractmethod
    def upsert_document(self, document_id: str, chunks: List[Dict[str, Any]]) -> int:
        ...

    @abstractmethod
    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        ...

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        ...

    @abstractmethod
    def delete_chunk(self, chunk_id: str) -> bool:
        ...

    @abstractmethod
    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def count(self) -> int:
        ...

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def close(self) -> None:
        ...
