import elasticsearch
from elasticsearch import Elasticsearch
import logging
import json
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Connect to Elasticsearch
    try:
        es = Elasticsearch("http://localhost:9200")
        info = es.info()
        logger.info(f"Connected to Elasticsearch successfully: {info['version']['number']}")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        return

    # Create a sample document with comments
    sample_doc = {
        "issue_key": "TEST-123",
        "summary": "Test issue with comments",
        "description": "This is a test issue to verify comment structure",
        "issue_type": "Task",
        "status": "Open",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "comments": [
            {
                "body": "This is the first comment",
                "author": "test_user1",
                "created_at": datetime.now().isoformat()
            },
            {
                "body": "This is a reply to the first comment",
                "author": "test_user2",
                "created_at": datetime.now().isoformat()
            },
            {
                "body": "This is a longer comment with some specific details about the issue.\nIt has multiple lines and contains some Polish characters: ąęćłńóśźż",
                "author": "test_user3",
                "created_at": datetime.now().isoformat()
            }
        ]
    }
    
    # Insert the document
    try:
        response = es.index(index="jira-changelog", document=sample_doc)
        logger.info(f"Sample document inserted: {response['result']}, id: {response['_id']}")
    except Exception as e:
        logger.error(f"Failed to insert sample document: {str(e)}")
        return
    
    # Wait for indexing
    es.indices.refresh(index="jira-changelog")
    logger.info("Index refreshed")
    
    # Retrieve the document
    try:
        query = {"match": {"issue_key": "TEST-123"}}
        response = es.search(index="jira-changelog", query=query)
        if response["hits"]["total"]["value"] > 0:
            doc = response["hits"]["hits"][0]["_source"]
            logger.info(f"Retrieved document: {doc['issue_key']}")
            
            # Check comments structure
            if "comments" in doc:
                logger.info(f"Comments found: {len(doc['comments'])}")
                logger.info("Comments structure:")
                print(json.dumps(doc["comments"], indent=2))
            else:
                logger.warning("No comments found in the document")
        else:
            logger.warning("Document not found")
    except Exception as e:
        logger.error(f"Failed to retrieve document: {str(e)}")
    
    # Try querying for comments
    try:
        nested_query = {
            "nested": {
                "path": "comments",
                "query": {
                    "match": {
                        "comments.body": "first comment"
                    }
                }
            }
        }
        
        response = es.search(index="jira-changelog", query=nested_query)
        logger.info(f"Nested query results: {response['hits']['total']['value']} documents found")
        
        if response["hits"]["total"]["value"] > 0:
            for hit in response["hits"]["hits"]:
                logger.info(f"Found issue: {hit['_source']['issue_key']}")
    except Exception as e:
        logger.error(f"Failed to execute nested query: {str(e)}")

if __name__ == "__main__":
    main()
