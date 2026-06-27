import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, Range

from .base import VectorStore
from .exceptions import CollectionError, ConnectionError, IndexError, VectorStoreError
from .collection_manager import CollectionManager
from .metadata_mapper import MetadataMapper

logger = logging.getLogger(__name__)


def _chunk_id_to_uuid(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = MetadataMapper.COLLECTION_NAME,
        vector_dimension: int = 768,
        distance_metric: str = "Cosine",
        local_path: Optional[str] = None,
    ):
        self._host = host
        self._port = port
        self._collection_name = collection_name
        self._vector_dimension = vector_dimension
        self._distance_metric = distance_metric
        self._local_path = local_path
        self._client: Optional[Any] = None
        self._collection_manager: Optional[CollectionManager] = None
        self._mapper = MetadataMapper()

    def initialize(self) -> None:
        if self._client is not None:
            logger.debug("QdrantVectorStore already initialized")
            return

        start = time.time()
        logger.info(
            "Connecting to Qdrant: host=%s, port=%d, local_path=%s, collection=%s",
            self._host, self._port, self._local_path or "(none)", self._collection_name,
        )

        try:
            if self._local_path:
                self._client = QdrantClient(path=self._local_path)
                logger.info("Local Qdrant instance at '%s'", self._local_path)
            else:
                self._client = QdrantClient(host=self._host, port=self._port)
                logger.info("Connected to Qdrant at %s:%d", self._host, self._port)
        except Exception as e:
            logger.error("Failed to connect to Qdrant: %s", e)
            raise ConnectionError(f"Failed to connect to Qdrant: {e}")

        self._collection_manager = CollectionManager(
            client=self._client,
            collection_name=self._collection_name,
            vector_dimension=self._vector_dimension,
            distance_metric=self._distance_metric,
        )

        self._collection_manager.initialize()

        elapsed = time.time() - start
        logger.info(
            "QdrantVectorStore initialized: collection=%s, elapsed=%.2fs",
            self._collection_name, elapsed,
        )

    def create_collection(self) -> None:
        self._ensure_initialized()
        self._collection_manager._create_collection()

    def delete_collection(self) -> None:
        self._ensure_initialized()
        self._collection_manager.delete_collection()

    def collection_exists(self) -> bool:
        if self._client is None:
            return False
        if self._collection_manager is None:
            return False
        return self._collection_manager.collection_exists()

    def upsert_document(self, document_id: str, chunks: List[Dict[str, Any]]) -> int:
        self._ensure_initialized()
        if not chunks:
            logger.warning("No chunks to upsert for document '%s'", document_id)
            return 0

        start = time.time()
        points = []
        for chunk in chunks:
            chunk["document_id"] = document_id
            vector = chunk.get("vector", [])
            if not vector:
                logger.warning("Chunk '%s' has no vector, skipping", chunk.get("chunk_id"))
                continue

            chunk_id = chunk.get("chunk_id", "")
            embedding_version = chunk.get("embedding_version", "")
            checksum = chunk.get("checksum", "")
            point_data = MetadataMapper.chunk_to_point(
                chunk, vector,
                embedding_version=embedding_version,
                checksum=checksum,
            )
            points.append(PointStruct(
                id=_chunk_id_to_uuid(chunk_id),
                vector=point_data["vector"],
                payload=point_data["payload"],
            ))

        if not points:
            return 0

        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            )
            elapsed = time.time() - start
            logger.info(
                "Upserted %d points for document '%s': collection=%s, elapsed=%.2fs",
                len(points), document_id, self._collection_name, elapsed,
            )
            return len(points)
        except Exception as e:
            logger.error("Failed to upsert document '%s': %s", document_id, e)
            raise IndexError(f"Failed to upsert document: {e}")

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        self._ensure_initialized()
        if not chunks:
            return 0

        start = time.time()
        points = []
        for chunk in chunks:
            vector = chunk.get("vector", [])
            if not vector:
                continue

            chunk_id = chunk.get("chunk_id", "")
            embedding_version = chunk.get("embedding_version", "")
            checksum = chunk.get("checksum", "")
            point_data = MetadataMapper.chunk_to_point(
                chunk, vector,
                embedding_version=embedding_version,
                checksum=checksum,
            )
            points.append(PointStruct(
                id=_chunk_id_to_uuid(chunk_id),
                vector=point_data["vector"],
                payload=point_data["payload"],
            ))

        if not points:
            return 0

        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            )
            elapsed = time.time() - start
            logger.info(
                "Upserted %d chunks: collection=%s, elapsed=%.2fs",
                len(points), self._collection_name, elapsed,
            )
            return len(points)
        except Exception as e:
            logger.error("Failed to upsert chunks: %s", e)
            raise IndexError(f"Failed to upsert chunks: {e}")

    def delete_document(self, document_id: str) -> bool:
        self._ensure_initialized()
        start = time.time()

        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        ),
                    ],
                ),
            )
            elapsed = time.time() - start
            logger.info(
                "Deleted document '%s': collection=%s, elapsed=%.2fs",
                document_id, self._collection_name, elapsed,
            )
            return True
        except Exception as e:
            logger.error("Failed to delete document '%s': %s", document_id, e)
            raise IndexError(f"Failed to delete document: {e}")

    def delete_chunk(self, chunk_id: str) -> bool:
        self._ensure_initialized()
        start = time.time()

        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=[_chunk_id_to_uuid(chunk_id)],
            )
            elapsed = time.time() - start
            logger.info(
                "Deleted chunk '%s': collection=%s, elapsed=%.2fs",
                chunk_id, self._collection_name, elapsed,
            )
            return True
        except Exception as e:
            logger.error("Failed to delete chunk '%s': %s", chunk_id, e)
            raise IndexError(f"Failed to delete chunk: {e}")

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_initialized()
        start = time.time()

        try:
            points = self._client.retrieve(
                collection_name=self._collection_name,
                ids=[_chunk_id_to_uuid(chunk_id)],
            )
            elapsed = time.time() - start

            if not points:
                logger.debug("Chunk '%s' not found (%.2fs)", chunk_id, elapsed)
                return None

            point = points[0]
            result = MetadataMapper.payload_to_chunk(point.payload or {})
            result["vector"] = point.vector if hasattr(point, "vector") else []
            logger.debug("Retrieved chunk '%s' (%.2fs)", chunk_id, elapsed)
            return result
        except Exception as e:
            logger.error("Failed to get chunk '%s': %s", chunk_id, e)
            raise IndexError(f"Failed to get chunk: {e}")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        start = time.time()

        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = MetadataMapper.build_qdrant_filter(filter_conditions)

        try:
            response = self._client.query_points(
                collection_name=self._collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
                with_vectors=True,
            )
            results = response.points
            elapsed = time.time() - start
            logger.info(
                "Search completed: top_k=%d, filter=%s, results=%d, elapsed=%.2fs",
                top_k, bool(filter_conditions), len(results), elapsed,
            )

            output = []
            for scored in results:
                chunk = MetadataMapper.payload_to_chunk(scored.payload or {})
                chunk["score"] = scored.score
                chunk["vector"] = scored.vector if hasattr(scored, "vector") else []
                output.append(chunk)
            return output
        except Exception as e:
            logger.error("Search failed: %s", e)
            raise IndexError(f"Search failed: {e}")

    def count(self) -> int:
        if self._client is None:
            return 0
        try:
            info = self._client.get_collection(self._collection_name)
            return info.points_count
        except Exception as e:
            logger.error("Failed to count vectors: %s", e)
            return 0

    def health(self) -> Dict[str, Any]:
        try:
            from importlib.metadata import version as lib_version
            qdrant_version = lib_version("qdrant-client")
        except Exception:
            qdrant_version = "unknown"

        healthy = False
        collection_ok = False
        vector_count = 0

        try:
            if self._client is None:
                return {
                    "status": "not_initialized",
                    "collection": self._collection_name,
                    "vectors": 0,
                    "version": qdrant_version,
                }

            version_info = self._client.get_collection(self._collection_name)
            collection_ok = True
            vector_count = version_info.points_count
            healthy = True
        except Exception:
            healthy = False

        return {
            "status": "healthy" if healthy else "unhealthy",
            "collection": self._collection_name,
            "vectors": vector_count,
            "collection_exists": collection_ok,
            "client_version": qdrant_version,
        }

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Qdrant connection closed")
            except Exception as e:
                logger.warning("Error closing Qdrant connection: %s", e)
            self._client = None
            self._collection_manager = None

    def _ensure_initialized(self) -> None:
        if self._client is None:
            self.initialize()
