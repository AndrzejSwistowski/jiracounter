"""
Extension for JiraElasticsearchPopulator with additional methods for index management.
This file provides methods to explicitly create indices with mappings from es_mapping.py.
"""

import logging
from es_utils import create_index as utils_create_index

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
    # Use the centralized create_index function from es_utils.py
    return utils_create_index(populator=self, index_name=index_name, mapping=mapping, logger=logger)

# To use this extension, add this method to the JiraElasticsearchPopulator class.
# This will delegate to the centralized create_index function in es_utils.py:
# JiraElasticsearchPopulator.create_index = create_index
