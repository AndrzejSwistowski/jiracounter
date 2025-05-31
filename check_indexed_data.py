#!/usr/bin/env python3
"""
Script to check if data was properly indexed in Elasticsearch.
"""

import logging
from elasticsearch import Elasticsearch
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Check Elasticsearch indices for data."""
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(["http://localhost:9200"])
        
        # Check if ES is running
        if not es.ping():
            logger.error("Cannot connect to Elasticsearch")
            return
            
        logger.info("Successfully connected to Elasticsearch")
        
        # Check indices
        indices = es.cat.indices(format="json")
        logger.info(f"Available indices: {[idx['index'] for idx in indices]}")
        
        # Check document count
        for index in ["jira-changelog", "jira-settings"]:
            try:
                count = es.count(index=index)
                logger.info(f"Index {index} has {count['count']} documents")
            except Exception as e:
                logger.error(f"Error getting count for {index}: {e}")
        
        # Search for some documents in jira-changelog
        try:
            result = es.search(
                index="jira-changelog",
                body={
                    "query": {"match_all": {}},
                    "size": 5,
                    "_source": ["issue.key", "issue.type.name", "issue.status.name", "@timestamp"]
                }
            )
            
            hits = result["hits"]["hits"]
            logger.info(f"Found {len(hits)} documents in jira-changelog:")
            
            for hit in hits:
                source = hit["_source"]
                logger.info(f"Document ID: {hit['_id']}")
                logger.info(f"  Issue Key: {source.get('issue', {}).get('key')}")
                logger.info(f"  Issue Type: {source.get('issue', {}).get('type', {}).get('name')}")
                logger.info(f"  Status: {source.get('issue', {}).get('status', {}).get('name')}")
                logger.info(f"  Timestamp: {source.get('@timestamp')}")
                logger.info("---")
        except Exception as e:
            logger.error(f"Error searching jira-changelog: {e}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        
if __name__ == "__main__":
    main()
