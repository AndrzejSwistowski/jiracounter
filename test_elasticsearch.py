#!/usr/bin/env python3
"""
Simple test script to verify Elasticsearch connection.
This will attempt to connect to Elasticsearch and list available indices.
"""

import logging
import requests
import json
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def test_elasticsearch_connection():
    """Test connection to Elasticsearch."""
    es_config = config.get_elasticsearch_config()
    
    # Build the connection URL
    if es_config['url']:
        url = es_config['url'].rstrip('/')
    else:
        url = f"http://{es_config['host']}:{es_config['port']}"
    
    logger.info(f"Testing connection to Elasticsearch at {url}")
    
    # Prepare headers for HTTP requests
    headers = {"Content-Type": "application/json"}
    if es_config['api_key']:
        headers["Authorization"] = f"ApiKey {es_config['api_key']}"
        logger.info("Using API key authentication")
    
    try:
        # Test connection with cluster health
        response = requests.get(f"{url}/_cluster/health", headers=headers, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info("Successfully connected to Elasticsearch!")
            logger.info(f"Cluster: {health_data['cluster_name']} / Status: {health_data['status']}")
            
            # Get cluster info
            info_response = requests.get(f"{url}/", headers=headers)
            if info_response.status_code == 200:
                info = info_response.json()
                logger.info(f"Version: {info['version']['number']}")
            
            # List indices
            indices_response = requests.get(f"{url}/_cat/indices?format=json", headers=headers)
            if indices_response.status_code == 200:
                indices = indices_response.json()
                logger.info(f"Found {len(indices)} indices")
                
                # Print first 10 indices
                for i, index_info in enumerate(sorted(indices, key=lambda x: x['index'])):
                    if i < 10:
                        logger.info(f"  - {index_info['index']}")
                    else:
                        break
                        
                if len(indices) > 10:
                    logger.info(f"  ... and {len(indices) - 10} more")
            else:
                logger.warning(f"Failed to get indices list: {indices_response.status_code}")
                
            return True
        else:
            logger.error(f"Failed to connect to Elasticsearch: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        return False

if __name__ == "__main__":
    test_elasticsearch_connection()