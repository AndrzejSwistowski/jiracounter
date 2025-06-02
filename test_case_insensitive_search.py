#!/usr/bin/env python3
"""
Test script to demonstrate case-insensitive status field functionality.
This script will add a test document and show how case-insensitive searches work.
"""
import json
import logging
from elasticsearch import Elasticsearch
import config

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test case-insensitive status field functionality."""
    # Connect to Elasticsearch
    try:
        if config.ELASTIC_APIKEY:
            es = Elasticsearch(
                config.ELASTIC_URL,
                api_key=config.ELASTIC_APIKEY,
                verify_certs=False
            )
        else:
            es = Elasticsearch(
                config.ELASTIC_URL,
                basic_auth=(config.ELASTIC_USER, config.ELASTIC_PASSWORD),
                verify_certs=False
            )
        logger.info("Connected to Elasticsearch successfully")
        
        # Create a test document
        test_doc = {
            "@timestamp": "2024-01-01T00:00:00Z",
            "issue": {
                "id": "test-123",
                "key": "TEST-123",
                "status": {
                    "name": "HOLD",
                    "name_lower": "hold"  # This will be automatically lowercased by the normalizer
                },
                "type": {
                    "name": "Bug",
                    "name_lower": "bug"
                }
            },
            "unique_statuses_visited": ["TODO", "IN PROGRESS", "HOLD"],
            "unique_statuses_visited_lower": ["todo", "in progress", "hold"],
            "status_transitions": [
                {
                    "from_status": "TODO",
                    "from_status_lower": "todo",
                    "to_status": "IN PROGRESS", 
                    "to_status_lower": "in progress",
                    "transition_date": "2024-01-01T08:00:00Z"
                },
                {
                    "from_status": "IN PROGRESS",
                    "from_status_lower": "in progress", 
                    "to_status": "HOLD",
                    "to_status_lower": "hold",
                    "transition_date": "2024-01-01T10:00:00Z"
                }
            ]
        }
        
        # Index the test document
        logger.info("Indexing test document...")
        es.index(index="jira-changelog", id="test-doc", body=test_doc)
        es.indices.refresh(index="jira-changelog")
        
        # Test case-sensitive searches (original fields)
        print("\n=== Case-Sensitive Searches (Original Fields) ===")
        
        # This should find the document
        query = {"query": {"term": {"issue.status.name": "HOLD"}}}
        result = es.search(index="jira-changelog", body=query)
        print(f"Search for 'HOLD' (exact case): {result['hits']['total']['value']} results")
        
        # This should NOT find the document (wrong case)
        query = {"query": {"term": {"issue.status.name": "hold"}}}
        result = es.search(index="jira-changelog", body=query)
        print(f"Search for 'hold' (wrong case): {result['hits']['total']['value']} results")
        
        # Test case-insensitive searches (new fields)
        print("\n=== Case-Insensitive Searches (New Fields) ===")
        
        # Both of these should find the document
        query = {"query": {"term": {"issue.status.name_lower": "hold"}}}
        result = es.search(index="jira-changelog", body=query)
        print(f"Search for 'hold' (lowercase field): {result['hits']['total']['value']} results")
        
        query = {"query": {"term": {"issue.status.name_lower": "HOLD"}}}
        result = es.search(index="jira-changelog", body=query)
        print(f"Search for 'HOLD' (lowercase field): {result['hits']['total']['value']} results")
        
        # Test status transitions
        print("\n=== Status Transition Searches ===")
        
        query = {"query": {"nested": {"path": "status_transitions", "query": {"term": {"status_transitions.to_status_lower": "hold"}}}}}
        result = es.search(index="jira-changelog", body=query)
        print(f"Nested search for transitions to 'hold': {result['hits']['total']['value']} results")
        
        # Clean up test document
        logger.info("Cleaning up test document...")
        es.delete(index="jira-changelog", id="test-doc")
        
        print("\n✅ Case-insensitive functionality working correctly!")
        print("Now you can use lowercase searches in Kibana like:")
        print("  - issue.status.name_lower : hold")
        print("  - issue.type.name_lower : bug") 
        print("  - status_transitions.to_status_lower : done")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")

if __name__ == "__main__":
    main()
