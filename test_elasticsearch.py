#!/usr/bin/env python3
"""
Simple test script to verify Elasticsearch connection.
This will attempt to connect to Elasticsearch and list available indices.
"""

import logging
from elasticsearch import Elasticsearch
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
        connection_url = es_config['url']
    else:
        connection_url = f"http://{es_config['host']}:{es_config['port']}"
    
    logger.info(f"Testing connection to Elasticsearch at {connection_url}")
    
    # Remove trailing slash if present
    url = connection_url.rstrip('/')
    
    # Prepare connection arguments
    connect_args = {
        'hosts': [url]
    }
    
    # Add API key authentication if provided
    if es_config['api_key']:
        connect_args['headers'] = {
            "Authorization": f"ApiKey {es_config['api_key']}"
        }
        logger.info("Using API key authentication")
    
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(**connect_args)
        
        # Check connection with ping
        if es.ping():
            logger.info("Successfully connected to Elasticsearch!")
            
            # Get cluster info
            info = es.info()
            logger.info(f"Cluster: {info['cluster_name']} / Version: {info['version']['number']}")
            
            # List indices
            indices = es.indices.get_alias(index="*")
            logger.info(f"Found {len(indices)} indices")
            
            # Print first 10 indices
            for i, index_name in enumerate(sorted(indices.keys())):
                if i < 10:
                    logger.info(f"  - {index_name}")
                else:
                    break
                    
            if len(indices) > 10:
                logger.info(f"  ... and {len(indices) - 10} more")
                
            return True
        else:
            logger.error("Failed to ping Elasticsearch")
            return False
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        return False

if __name__ == "__main__":
    test_elasticsearch_connection()