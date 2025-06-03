#!/usr/bin/env python3
"""
Elasticsearch utility functions for common operations.
These utilities provide a centralized place for common Elasticsearch operations
and can be imported by other modules to avoid code duplication.
"""

import logging
import requests
import json  # Add json import for the create_index function

def _setup_es_connection(host=None, port=None, api_key=None, use_ssl=True, url=None, populator=None):
    """
    Setup Elasticsearch connection parameters and return base URL and headers.
    
    Args:
        host (str): Elasticsearch host
        port (int): Elasticsearch port
        api_key (str): Elasticsearch API key
        use_ssl (bool): Whether to use SSL for the connection
        url (str): Complete Elasticsearch URL
        populator: An instance of JiraElasticsearchPopulator
        
    Returns:
        tuple: (base_url, headers) for Elasticsearch requests
    """
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
    
    return base_url, headers

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
        base_url, headers = _setup_es_connection(host, port, api_key, use_ssl, url, populator)
        
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

def create_index_with_fallback(host=None, port=None, api_key=None, use_ssl=True, url=None,
                              index_name=None, mappings=None, logger=None, populator=None):
    """
    Create an Elasticsearch index with fallback support for multiple mapping types.
    
    This function attempts to create an index with the primary mapping first, then falls back
    to alternative mappings if the primary fails (e.g., Polish analyzer not available).
    
    Args:
        host (str): Elasticsearch host
        port (int): Elasticsearch port
        api_key (str): Elasticsearch API key
        use_ssl (bool): Whether to use SSL for the connection
        url (str): Complete Elasticsearch URL
        index_name (str): Name of the index to create
        mappings (list): List of mapping dictionaries to try in order [primary, fallback1, fallback2, ...]
        logger (logging.Logger): Logger object
        populator: An instance of JiraElasticsearchPopulator
        
    Returns:
        bool: True if the index was created successfully, False if all attempts failed
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if not mappings:
        logger.error("No mappings provided for index creation")
        return False
    
    # Ensure mappings is a list
    if not isinstance(mappings, list):
        mappings = [mappings]
    
    # Try each mapping in order
    for i, mapping in enumerate(mappings):
        try:
            mapping_name = f"mapping #{i+1}" if i > 0 else "primary mapping"
            logger.info(f"Attempting to create index {index_name} with {mapping_name}...")
            
            if create_index(host=host, port=port, api_key=api_key, use_ssl=use_ssl, url=url,
                           index_name=index_name, mapping=mapping, logger=logger, populator=populator):
                return True
            else:
                logger.warning(f"Failed to create index {index_name} with {mapping_name}")
                if i < len(mappings) - 1:
                    logger.info(f"Trying fallback mapping...")
        except Exception as e:
            logger.warning(f"Error with {mapping_name}: {e}")
            if i < len(mappings) - 1:
                logger.info(f"Trying fallback mapping...")
    
    logger.error(f"Failed to create index {index_name} with any of the provided mappings")
    return False


def create_index(host=None, port=None, api_key=None, use_ssl=True, url=None,
                index_name=None, mapping=None, logger=None, populator=None):
    """
    Create an Elasticsearch index with the specified mapping.
    
    This function can be called in two ways:
    1. With a populator object: create_index(populator=populator, index_name=index_name, mapping=mapping, logger=logger)
    2. With connection details: create_index(url=url, api_key=api_key, index_name=index_name, mapping=mapping, logger=logger)
       or create_index(host=host, port=port, use_ssl=use_ssl, api_key=api_key, index_name=index_name, mapping=mapping, logger=logger)
       
    Args:
        host (str): Elasticsearch host
        port (int): Elasticsearch port
        api_key (str): Elasticsearch API key
        use_ssl (bool): Whether to use SSL for the connection
        url (str): Complete Elasticsearch URL
        index_name (str): Name of the index to create
        mapping (dict): Mapping dictionary to apply to the index
        logger (logging.Logger): Logger object
        populator: An instance of JiraElasticsearchPopulator
        
    Returns:
        bool: True if the index was created successfully, False if there was an error
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    try:
        base_url, headers = _setup_es_connection(host, port, api_key, use_ssl, url, populator)
        
        # Check if index already exists
        try:
            index_check_response = requests.head(f"{base_url}/{index_name}", headers=headers)
            if index_check_response.status_code == 200:
                logger.info(f"Index {index_name} already exists, skipping creation")
                return True
        except Exception as e:
            logger.warning(f"Error checking if index exists: {e}")
        
        # Create the index with mapping
        logger.info(f"Creating index {index_name} with explicit mapping...")
        
        # Send PUT request to create the index with mapping
        create_response = requests.put(
            f"{base_url}/{index_name}", 
            headers=headers,
            json=mapping,
            timeout=30
        )
        
        if create_response.status_code in [200, 201]:
            logger.info(f"Successfully created index {index_name} with explicit mapping")
            return True
        else:
            logger.error(f"Failed to create index {index_name}: {create_response.status_code} - {create_response.text}")
            return False
    except Exception as e:
        logger.error(f"Error creating index {index_name}: {e}")
        return False


def get_mapping_fallback_chain(index_name):
    """
    Get the appropriate mapping fallback chain for a given index.
    
    Args:
        index_name (str): Name of the index
        
    Returns:
        list: List of mappings to try in order (primary to fallback)
    """
    import config
    
    # Import mappings
    try:
        from es_mapping_polish import CHANGELOG_MAPPING_POLISH, SETTINGS_MAPPING_POLISH
        polish_available = True
    except ImportError:
        polish_available = False
    
    try:
        from es_mapping_simple import CHANGELOG_MAPPING_SIMPLE, SETTINGS_MAPPING_SIMPLE
        simple_available = True
    except ImportError:
        simple_available = False
    
    try:
        from es_mapping import CHANGELOG_MAPPING, SETTINGS_MAPPING
        basic_available = True
    except ImportError:
        basic_available = False
    
    # Build fallback chain based on index type
    mappings = []
    
    if index_name == getattr(config, 'INDEX_CHANGELOG', 'jira-changelog'):
        # Changelog index mapping priority: Polish > Simple > Basic
        if polish_available:
            mappings.append(CHANGELOG_MAPPING_POLISH)
        if simple_available:
            mappings.append(CHANGELOG_MAPPING_SIMPLE)
        if basic_available:
            mappings.append(CHANGELOG_MAPPING)
    elif index_name == getattr(config, 'INDEX_SETTINGS', 'jira-settings'):
        # Settings index mapping priority: Polish > Simple > Basic
        if polish_available:
            mappings.append(SETTINGS_MAPPING_POLISH)
        if simple_available:
            mappings.append(SETTINGS_MAPPING_SIMPLE)
        if basic_available:
            mappings.append(SETTINGS_MAPPING)
    
    if not mappings:
        raise ValueError(f"No mappings available for index {index_name}")
    
    return mappings


def create_index_with_auto_fallback(host=None, port=None, api_key=None, use_ssl=True, url=None,
                                   index_name=None, logger=None, populator=None):
    """
    Create an Elasticsearch index with automatic mapping fallback.
    
    This function automatically determines the best mapping chain for the given index
    and attempts to create it with fallback support.
    
    Args:
        host (str): Elasticsearch host
        port (int): Elasticsearch port
        api_key (str): Elasticsearch API key
        use_ssl (bool): Whether to use SSL for the connection
        url (str): Complete Elasticsearch URL
        index_name (str): Name of the index to create
        logger (logging.Logger): Logger object
        populator: An instance of JiraElasticsearchPopulator
        
    Returns:
        bool: True if the index was created successfully, False if all attempts failed
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        mappings = get_mapping_fallback_chain(index_name)
        return create_index_with_fallback(
            host=host, port=port, api_key=api_key, use_ssl=use_ssl, url=url,
            index_name=index_name, mappings=mappings, logger=logger, populator=populator
        )
    except Exception as e:
        logger.error(f"Error creating index {index_name} with auto fallback: {e}")
        return False
