import logging
from typing import Any, Dict, Optional

from qdrant_client.http.models import Distance, VectorParams

from .exceptions import CollectionError
from .metadata_mapper import MetadataMapper

logger = logging.getLogger(__name__)


class CollectionManager:
    def __init__(
        self,
        client: Any,
        collection_name: str = MetadataMapper.COLLECTION_NAME,
        vector_dimension: int = 768,
        distance_metric: str = "Cosine",
    ):
        self._client = client
        self._collection_name = collection_name
        self._vector_dimension = vector_dimension
        self._distance_metric = distance_metric

    def initialize(self) -> None:
        if self.collection_exists():
            info = self._get_collection_info()
            existing_dim = info.get("vector_dimension", 0)
            existing_dist = info.get("distance_metric", "")

            if existing_dim != self._vector_dimension:
                raise CollectionError(
                    f"Dimension mismatch: collection has {existing_dim}, "
                    f"config requires {self._vector_dimension}",
                )

            if existing_dist.lower() != self._distance_metric.lower():
                logger.warning(
                    "Distance metric mismatch: collection uses '%s', config has '%s'",
                    existing_dist, self._distance_metric,
                )

            logger.info(
                "Collection '%s' exists: dimension=%d, distance=%s",
                self._collection_name, existing_dim, existing_dist,
            )
        else:
            self._create_collection()

    def collection_exists(self) -> bool:
        try:
            result = self._client.get_collection(self._collection_name)
            return result is not None
        except Exception:
            return False

    def _create_collection(self) -> None:
        logger.info(
            "Creating collection '%s': dimension=%d, distance=%s",
            self._collection_name, self._vector_dimension, self._distance_metric,
        )

        distance_map = {
            "cosine": Distance.COSINE,
            "dot": Distance.DOT,
            "euclid": Distance.EUCLID,
        }

        distance = distance_map.get(self._distance_metric.lower(), Distance.COSINE)

        try:
            self._client.recreate_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=self._vector_dimension,
                    distance=distance,
                ),
            )
            logger.info("Collection '%s' created successfully", self._collection_name)
        except Exception as e:
            logger.error("Failed to create collection '%s': %s", self._collection_name, e)
            raise CollectionError(f"Failed to create collection: {e}")

    def delete_collection(self) -> None:
        try:
            self._client.delete_collection(self._collection_name)
            logger.info("Collection '%s' deleted", self._collection_name)
        except Exception as e:
            logger.error("Failed to delete collection '%s': %s", self._collection_name, e)
            raise CollectionError(f"Failed to delete collection: {e}")

    def _get_collection_info(self) -> Dict[str, Any]:
        try:
            info = self._client.get_collection(self._collection_name)
            config = info.config
            params = config.params.vectors
            return {
                "vector_dimension": params.size,
                "distance_metric": str(params.distance),
            }
        except Exception as e:
            logger.error("Failed to get collection info: %s", e)
            return {}

    def get_info(self) -> Dict[str, Any]:
        info = self._get_collection_info()
        return {
            "collection_name": self._collection_name,
            "vector_dimension": info.get("vector_dimension", 0),
            "distance_metric": info.get("distance_metric", ""),
            "exists": self.collection_exists(),
            "vectors": self._get_vector_count(),
        }

    def _get_vector_count(self) -> int:
        try:
            info = self._client.get_collection(self._collection_name)
            return info.points_count
        except Exception:
            return 0
