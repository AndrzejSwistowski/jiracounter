#!/usr/bin/env python3
"""
Elasticsearch utility functions for common operations.
These utilities provide a centralized place for common Elasticsearch operations
and can be imported by other modules to avoid code duplication.
"""

import logging
import requests

def delete_index(host=None, port=None, api_key=None, use_ssl=True, url=None, 
                 index_name=None, logger=None, populator=None):
    """
    Delete an Elasticsearch index.
    
    This function can be called in two ways:
    1. With a populator object: delete_index(populator=populator, index_name=index_name, logger=logger)
    2. With connection details: delete_index(url=url, api_key=api_key, index_name=index_name, logger=logger)
       or delete_index(host=host, port=port, use_ssl=use_ssl, api_key=api_key, index_name=index_name, logger=logger)
       
    Args:
        host (str): Elasticsearch host
        port (int): Elasticsearch port
        api_key (str): Elasticsearch API key
        use_ssl (bool): Whether to use SSL for the connection
        url (str): Complete Elasticsearch URL
        index_name (str): Name of the index to delete
        logger (logging.Logger): Logger object
        populator: An instance of JiraElasticsearchPopulator
        
    Returns:
        bool: True if the index was deleted or doesn't exist, False if there was an error
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    try:
        # If populator is provided, extract connection parameters from it
        if populator:
            if url is None:
                url = populator.url
            if host is None:
                host = populator.host
            if port is None:
                port = populator.port
            if api_key is None:
                api_key = populator.api_key
            if use_ssl is None:
                use_ssl = populator.use_ssl
        
        # Build base URL if not provided
        if url:
            base_url = url.rstrip('/')
        else:
            base_url = f'{"https" if use_ssl else "http"}://{host}:{port}'
            
        # Prepare headers with API key authentication
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"ApiKey {api_key}"
        
        # Delete the index
        logger.info(f"Deleting index {index_name}...")
        delete_response = requests.delete(f"{base_url}/{index_name}", headers=headers)
        
        if delete_response.status_code == 200:
            logger.info(f"Successfully deleted index {index_name}")
            return True
        elif delete_response.status_code == 404:
            logger.info(f"Index {index_name} does not exist, nothing to delete")
            return True
        else:
            logger.error(f"Failed to delete index {index_name}: {delete_response.status_code} - {delete_response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting index {index_name}: {e}")
        return False
