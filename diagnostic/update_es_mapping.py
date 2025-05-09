#!/usr/bin/env python
"""
Script to update the Elasticsearch mapping with the missing fields
(summary, labels, and components).
"""

import os
import logging
from elasticsearch import Elasticsearch, NotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get Elasticsearch settings from environment variables
    elastic_url = os.environ.get('ELASTIC_URL')
    elastic_apikey = os.environ.get('ELASTIC_APIKEY')
    
    if not elastic_url:
        logger.error("ELASTIC_URL environment variable not set")
        return
    
    # Connect to Elasticsearch
    headers = {}
    if elastic_apikey:
        headers["Authorization"] = f"ApiKey {elastic_apikey}"
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
                    "summary": {
                        "type": "text", 
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "labels": {
                        "type": "keyword"
                    },
                    "components": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "keyword"},
                            "name": {"type": "keyword"}
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
                logger.info("Successfully updated mapping with new fields")
            else:
                logger.error("Failed to update mapping")
            
            # Confirm the update
            mapping = es.indices.get_mapping(index="jira-changelog")
            mapping_dict = mapping.body
            properties = mapping_dict["jira-changelog"]["mappings"]["properties"]
            
            # Check if the fields were added successfully
            fields_added = all(field in properties for field in ["summary", "labels", "components"])
            if fields_added:
                logger.info("All fields were successfully added to the mapping")
                logger.info("You'll need to repopulate the index to see data in these fields")
            else:
                missing = [f for f in ["summary", "labels", "components"] if f not in properties]
                logger.error(f"Some fields were not added: {missing}")
        else:
            logger.error("jira-changelog index does not exist")
            
    except Exception as e:
        logger.error(f"Error updating Elasticsearch mapping: {e}")

if __name__ == "__main__":
    main()