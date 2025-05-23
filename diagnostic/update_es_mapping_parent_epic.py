#!/usr/bin/env python
"""
Script to update the Elasticsearch mapping with additional fields:
- parent_issue
- epic_issue
"""

import os
import sys
import logging
from elasticsearch import Elasticsearch, NotFoundError

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get Elasticsearch settings from centralized config
    es_config = config.get_elasticsearch_config()
    
    # Build the connection URL
    if es_config['url']:
        elastic_url = es_config['url']
    else:
        elastic_url = f"http://{es_config['host']}:{es_config['port']}"
    
    # Connect to Elasticsearch
    headers = {}
    if es_config['api_key']:
        headers["Authorization"] = f"ApiKey {es_config['api_key']}"
        logger.info("Using API key authentication")
    
    try:
        es = Elasticsearch(
            [elastic_url], 
            headers=headers
        )
        
        # Check if jira-changelog index exists
        if es.indices.exists(index="jira-changelog"):
            logger.info("jira-changelog index exists")
            
            # Define the mapping update for the new fields
            mapping_update = {
                "properties": {
                    "parent_issue": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "key": {"type": "keyword"},
                            "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "epic_issue": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "key": {"type": "keyword"},
                            "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    }
                }
            }
            
            # Update the mapping
            response = es.indices.put_mapping(
                index="jira-changelog",
                body=mapping_update
            )
            
            if response.get('acknowledged', False):
                logger.info("Successfully updated mapping with parent_issue and epic_issue fields")
            else:
                logger.error("Failed to update mapping")
            
            # Confirm the update
            mapping = es.indices.get_mapping(index="jira-changelog")
            mapping_dict = mapping.body
            properties = mapping_dict["jira-changelog"]["mappings"]["properties"]
            
            # Check if the fields were added successfully
            fields_added = all(field in properties for field in ["parent_issue", "epic_issue"])
            if fields_added:
                logger.info("All fields were successfully added to the mapping")
                logger.info("You'll need to repopulate the index to see data in these fields")
            else:
                missing = [f for f in ["parent_issue", "epic_issue"] if f not in properties]
                logger.error(f"Some fields were not added: {missing}")
        else:
            logger.error("jira-changelog index does not exist")
            
    except Exception as e:
        logger.error(f"Error updating Elasticsearch mapping: {e}")

if __name__ == "__main__":
    main()