"""Tests for the vector service."""

import os
import pytest
import numpy as np
from app.services.vector import VectorService

# Test collection name
TEST_COLLECTION = "test_collection"
VECTOR_DIM = 4  # Small dimension for testing

# Test data
TEST_VECTORS = [
    (1, [0.1, 0.2, 0.3, 0.4], {"text": "first", "category": "test"}),
    (2, [0.4, 0.3, 0.2, 0.1], {"text": "second", "category": "test"}),
    (3, [0.9, 0.8, 0.7, 0.6], {"text": "third", "category": "demo"}),
]

@pytest.fixture(scope="module")
def vector_service():
    """Fixture providing a vector service instance."""
    # Use environment variable or default to local Qdrant
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    service = VectorService(url=qdrant_url)
    
    # Ensure test collection exists
    service.ensure_collection(TEST_COLLECTION, VECTOR_DIM)
    
    # Clean up before tests
    service.client.delete_collection(TEST_COLLECTION)
    service.ensure_collection(TEST_COLLECTION, VECTOR_DIM)
    
    yield service
    
    # Clean up after tests
    try:
        service.client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
    service.close()

@pytest.fixture(scope="function")
def populated_vector_service(vector_service):
    """Fixture that populates the test collection with data."""
    # Add test vectors
    for vec_id, vector, payload in TEST_VECTORS:
        vector_service.upsert(TEST_COLLECTION, vec_id, vector, payload)
    
    yield vector_service
    
    # Clear the collection after test
    vector_service.client.delete_collection(TEST_COLLECTION)
    vector_service.ensure_collection(TEST_COLLECTION, VECTOR_DIM)

def test_ensure_collection(vector_service):
    """Test collection creation and existence check."""
    # Create a new collection
    collection_name = "test_new_collection"
    try:
        # Clean up in case it exists
        vector_service.client.delete_collection(collection_name)
    except Exception:
        pass
    
    # Test creation
    assert vector_service.ensure_collection(collection_name, VECTOR_DIM) is True
    
    # Test idempotency
    assert vector_service.ensure_collection(collection_name, VECTOR_DIM) is True
    
    # Clean up
    vector_service.client.delete_collection(collection_name)

def test_upsert_and_search(populated_vector_service):
    """Test vector upsert and search functionality."""
    service = populated_vector_service
    
    # Test search without filters
    query_vector = [0.15, 0.25, 0.35, 0.45]  # Close to first vector
    results = service.search(TEST_COLLECTION, query_vector, top_k=2)
    
    assert len(results) == 2
    assert results[0]["id"] == 1  # Should be closest to first vector
    assert results[0]["payload"]["text"] == "first"
    assert results[0]["score"] > 0.9  # Should be very similar

def test_search_with_filters(populated_vector_service):
    """Test search with filter conditions."""
    service = populated_vector_service
    query_vector = [0.15, 0.25, 0.35, 0.45]
    
    # Search with filter
    results = service.search(
        TEST_COLLECTION,
        query_vector,
        top_k=10,
        filter_conditions={"category": "demo"}
    )
    
    # Should only return the "demo" category vector
    assert len(results) == 1
    assert results[0]["id"] == 3
    assert results[0]["payload"]["text"] == "third"

def test_upsert_update(populated_vector_service):
    """Test that upsert updates existing vectors."""
    service = populated_vector_service
    
    # Update an existing vector
    updated_payload = {"text": "updated", "category": "test"}
    service.upsert(TEST_COLLECTION, 1, [0.1, 0.2, 0.3, 0.4], updated_payload)
    
    # Search and verify update
    results = service.search(
        TEST_COLLECTION,
        [0.1, 0.2, 0.3, 0.4],
        top_k=1,
        filter_conditions={"text": "updated"}
    )
    
    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["payload"]["text"] == "updated"
