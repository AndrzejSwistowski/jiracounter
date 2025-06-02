#!/usr/bin/env python3
"""
Script to check if data was properly indexed in Elasticsearch.
"""

import logging
import requests
import json
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Check Elasticsearch indices for data."""
    try:
        # Get Elasticsearch settings from centralized config
        es_config = config.get_elasticsearch_config()
        
        # Build the connection URL
        if es_config['url']:
            url = es_config['url'].rstrip('/')
        else:
            url = f"http://{es_config['host']}:{es_config['port']}"
        
        # Prepare headers for HTTP requests
        headers = {"Content-Type": "application/json"}
        if es_config['api_key']:
            headers["Authorization"] = f"ApiKey {es_config['api_key']}"
            logger.info("Using API key authentication")
        
        # Check if ES is running
        response = requests.get(f"{url}/_cluster/health", headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Cannot connect to Elasticsearch: {response.status_code}")
            return
            
        logger.info("Successfully connected to Elasticsearch")
        
        # Check indices
        indices_response = requests.get(f"{url}/_cat/indices?format=json", headers=headers)
        if indices_response.status_code == 200:
            indices = indices_response.json()
            logger.info(f"Available indices: {[idx['index'] for idx in indices]}")
        else:
            logger.error(f"Failed to get indices: {indices_response.status_code}")
        
        # Check document count
        for index in ["jira-changelog", "jira-settings"]:
            try:
                count_response = requests.get(f"{url}/{index}/_count", headers=headers)
                if count_response.status_code == 200:
                    count_data = count_response.json()
                    logger.info(f"Index {index} has {count_data['count']} documents")
                else:
                    logger.error(f"Error getting count for {index}: {count_response.status_code}")
            except Exception as e:
                logger.error(f"Error getting count for {index}: {e}")
        
        # Search for some documents in jira-changelog
        try:
            search_query = {
                "query": {"match_all": {}},
                "size": 5,
                "_source": ["issue.key", "issue.type.name", "issue.status.name", "@timestamp"]
            }
            
            search_response = requests.post(
                f"{url}/jira-changelog/_search",
                headers=headers,
                json=search_query
            )
            
            if search_response.status_code == 200:
                result = search_response.json()
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
            else:
                logger.error(f"Error searching jira-changelog: {search_response.status_code}")
        except Exception as e:
            logger.error(f"Error searching jira-changelog: {e}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        
if __name__ == "__main__":
    main()
