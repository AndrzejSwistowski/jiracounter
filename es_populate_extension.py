"""
Extension for JiraElasticsearchPopulator with additional methods for index management.
This file provides methods to explicitly create indices with mappings from es_mapping.py.
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)

def create_index(self, index_name, mapping):
    """
    Create an Elasticsearch index with the specified mapping.
    
    Args:
        index_name: Name of the index to create
        mapping: Mapping dictionary to apply to the index
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import requests
        import json
        
        # Build base URL
        if self.url:
            base_url = self.url.rstrip('/')
        else:
            base_url = f'{"https" if self.use_ssl else "http"}://{self.host}:{self.port}'
            
        # Prepare headers with API key authentication
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        
        # Create the index with mapping
        logger.info(f"Creating index {index_name} with explicit mapping...")
        
        # Convert mapping to JSON string
        mapping_json = json.dumps(mapping)
        
        # Send PUT request to create the index with mapping
        create_response = requests.put(
            f"{base_url}/{index_name}", 
            headers=headers,
            data=mapping_json
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

# To use this extension, add this method to the JiraElasticsearchPopulator class:
# JiraElasticsearchPopulator.create_index = create_index
