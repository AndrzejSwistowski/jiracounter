#!/usr/bin/env python3
"""
Simple test script to verify Elasticsearch connection using requests library.
This will attempt to connect to Elasticsearch and list available indices using the
same approach as the PowerShell script.
"""

import logging
import requests
import json
import config
from es_utils import _setup_es_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def test_elasticsearch_connection():
    """Test connection to Elasticsearch using requests library."""
    es_config = config.get_elasticsearch_config()
    
    # Setup connection using centralized helper
    url, headers = _setup_es_connection(
        host=es_config['host'],
        port=es_config['port'],
        api_key=es_config['api_key'],
        use_ssl=es_config.get('use_ssl', False),
        url=es_config['url']
    )
    
    logger.info(f"Testing connection to Elasticsearch at {url}")
    
    if es_config['api_key']:
        logger.info("Using API key authentication")
    
    try:
        # Test connection with a simple request to get cluster info
        response = requests.get(f"{url}/_cluster/health", headers=headers)
        
        if response.status_code == 200:
            logger.info("Successfully connected to Elasticsearch!")
            health_data = response.json()
            logger.info(f"Cluster: {health_data['cluster_name']} / Status: {health_data['status']}")
            
            # List indices
            indices_response = requests.get(f"{url}/_cat/indices?format=json", headers=headers)
            
            if indices_response.status_code == 200:
                indices = indices_response.json()
                logger.info(f"Found {len(indices)} indices")
                
                # Print first 10 indices
                for i, index in enumerate(indices):
                    if i < 10:
                        logger.info(f"  - {index['index']} ({index['health']})")
                    else:
                        break
                        
                if len(indices) > 10:
                    logger.info(f"  ... and {len(indices) - 10} more")
            else:
                logger.error(f"Failed to list indices: {indices_response.text}")
                
            return True
        else:
            logger.error(f"Failed to connect to Elasticsearch: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        return False

if __name__ == "__main__":
    test_elasticsearch_connection()