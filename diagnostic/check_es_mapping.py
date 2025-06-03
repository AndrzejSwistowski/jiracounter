#!/usr/bin/env python
"""
Script to check the Elasticsearch index mapping.
This will show us what fields already exist in the index.
"""

import os
import sys
import logging
import requests
import json

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from es_utils import _setup_es_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get Elasticsearch settings from centralized config
    es_config = config.get_elasticsearch_config()
    
    # Setup connection using centralized helper
    url, headers = _setup_es_connection(
        host=es_config['host'],
        port=es_config['port'],
        api_key=es_config['api_key'],
        use_ssl=es_config.get('use_ssl', False),
        url=es_config['url']
    )
    
    if es_config['api_key']:
        logger.info("Using API key authentication")
    
    try:
        # Test the connection
        response = requests.get(f"{url}/_cluster/health", headers=headers, timeout=10)
        if response.status_code != 200:
            raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code}")
        
        logger.info("Successfully connected to Elasticsearch")
        
        # Check if jira-changelog index exists
        index_response = requests.head(f"{url}/jira-changelog", headers=headers)
        if index_response.status_code == 200:
            logger.info("jira-changelog index exists")
            
            # Get the index mapping
            mapping_response = requests.get(f"{url}/jira-changelog/_mapping", headers=headers)
            if mapping_response.status_code != 200:
                logger.error(f"Failed to get mapping: {mapping_response.status_code}")
                return
            
            mapping = mapping_response.json()
            
            # Print the mapping in a readable format
            logger.info("Index mapping structure:")
            
            # Convert the mapping to a Python dictionary and extract properties
            if "jira-changelog" in mapping:
                properties = mapping["jira-changelog"]["mappings"]["properties"]
                logger.info(f"Found {len(properties)} top-level properties in the mapping")
                
                # List all top-level properties
                logger.info("Top-level fields in the index:")
                for field_name in properties.keys():
                    logger.info(f"  - {field_name}")
                
                # Check for specific fields
                if "summary" in properties:
                    logger.info(f"summary field exists with type: {properties['summary'].get('type')}")
                else:
                    logger.warning("summary field does not exist in the index")
                    
                if "labels" in properties:
                    logger.info(f"labels field exists with type: {properties['labels'].get('type')}")
                else:
                    logger.warning("labels field does not exist in the index")
                    
                if "components" in properties:
                    logger.info(f"components field exists with type: {properties['components'].get('type')}")
                else:
                    logger.warning("components field does not exist in the index")
            else:
                logger.warning("Unexpected mapping structure")
            
            # Get a sample document
            search_query = {
                "size": 1,
                "sort": [{"historyDate": {"order": "desc"}}]
            }
            
            search_response = requests.post(
                f"{url}/jira-changelog/_search",
                headers=headers,
                json=search_query
            )
            
            if search_response.status_code == 200:
                result = search_response.json()
                if result["hits"]["total"]["value"] > 0:
                    sample_doc = result["hits"]["hits"][0]["_source"]
                    logger.info("Found a sample document")
                    logger.info("Sample document fields:")
                    for field_name in sample_doc.keys():
                        logger.info(f"  - {field_name}")
                    
                    # Check for our specific fields in the sample document
                    logger.info("Checking for specific fields in the sample document:")
                    logger.info(f"  - summary: {'Present' if 'summary' in sample_doc else 'Missing'}")
                    logger.info(f"  - labels: {'Present' if 'labels' in sample_doc else 'Missing'}")
                    logger.info(f"  - components: {'Present' if 'components' in sample_doc else 'Missing'}")
                else:
                    logger.warning("No documents found in the index")
            else:
                logger.error(f"Failed to search documents: {search_response.status_code}")
        else:
            logger.warning("jira-changelog index does not exist")
    
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")

if __name__ == "__main__":
    main()