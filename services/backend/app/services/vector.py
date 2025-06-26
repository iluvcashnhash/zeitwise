"""
Qdrant vector database service for ZeitWise.

This module provides an interface to interact with Qdrant vector database,
handling vector operations like upserting and searching vectors.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

logger = logging.getLogger(__name__)


class VectorService:
    """Service for interacting with Qdrant vector database."""

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the Qdrant client.

        Args:
            url: Qdrant server URL. If not provided, will use QDRANT_URL from environment.
            api_key: Optional API key for authentication.
        """
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.client = self._init_client()
        logger.info(f"Initialized Qdrant client with URL: {self.url}")

    def _init_client(self) -> QdrantClient:
        """Initialize and return a Qdrant client instance."""
        try:
            client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=30.0,
            )
            # Test the connection
            client.get_collections()
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise

    def ensure_collection(self, name: str, dim: int) -> bool:
        """Ensure a collection exists with the given name and vector dimension.

        Args:
            name: Name of the collection.
            dim: Dimension of the vectors in the collection.

        Returns:
            bool: True if the collection was created or already exists, False otherwise.
        """
        try:
            collections = self.client.get_collections()
            collection_names = [collection.name for collection in collections.collections]

            if name not in collection_names:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=dim,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info(f"Created new collection: {name} with dimension: {dim}")
                return True
            
            logger.debug(f"Collection {name} already exists")
            return True

        except Exception as e:
            logger.error(f"Error ensuring collection {name}: {e}")
            return False

    def upsert(
        self, 
        collection_name: str, 
        id: Union[str, int], 
        vector: List[float], 
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Upsert a vector with the given ID and payload into the specified collection.

        Args:
            collection_name: Name of the collection to upsert into.
            id: Unique identifier for the vector.
            vector: The vector to upsert.
            payload: Optional metadata to associate with the vector.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            point = PointStruct(
                id=id,
                vector=vector,
                payload=payload or {}
            )
            self.client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=True
            )
            logger.debug(f"Upserted vector with ID: {id} to collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error upserting vector {id} to {collection_name}: {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in the specified collection.

        Args:
            collection_name: Name of the collection to search in.
            query_vector: The query vector for similarity search.
            top_k: Number of results to return.
            filter_conditions: Optional filter conditions for the search.

        Returns:
            List[Dict[str, Any]]: List of search results with scores.
        """
        try:
            # Convert filter conditions to Qdrant filter if provided
            query_filter = None
            if filter_conditions:
                must_conditions = []
                for field, value in filter_conditions.items():
                    must_conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value),
                        )
                    )
                query_filter = Filter(must=must_conditions)

            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_vectors=False,
                with_payload=True,
            )

            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                })

            logger.debug(f"Found {len(results)} results in collection: {collection_name}")
            return results

        except Exception as e:
            logger.error(f"Error searching in collection {collection_name}: {e}")
            return []

    def close(self):
        """Close the Qdrant client connection."""
        if hasattr(self, 'client') and self.client:
            self.client.close()
            logger.info("Closed Qdrant client connection")

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connections are closed when exiting context."""
        self.close()


# Singleton instance
vector_service = VectorService()
