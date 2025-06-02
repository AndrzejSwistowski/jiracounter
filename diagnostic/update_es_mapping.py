#!/usr/bin/env python
"""
Script to update the Elasticsearch mapping with the missing fields
(summary, labels, and components).
"""

import os
import sys
import logging
import requests
import json

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
        base_url = es_config['url'].rstrip('/')
    else:
        base_url = f"http://{es_config['host']}:{es_config['port']}"
    
    # Prepare headers for HTTP requests
    headers = {"Content-Type": "application/json"}
    if es_config['api_key']:
        headers["Authorization"] = f"ApiKey {es_config['api_key']}"
        logger.info("Using API key authentication")
    
    try:
        # Test the connection
        response = requests.get(f"{base_url}/_cluster/health", headers=headers, timeout=10)
        if response.status_code != 200:
            raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code}")
        
        # Check if jira-changelog index exists
        response = requests.head(f"{base_url}/jira-changelog", headers=headers, timeout=10)
        if response.status_code == 200:
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
            response = requests.put(
                f"{base_url}/jira-changelog/_mapping",
                headers=headers,
                json=mapping_update,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Successfully updated mapping with new fields")
            else:
                logger.error(f"Failed to update mapping: {response.status_code} - {response.text}")
            
            # Confirm the update
            response = requests.get(f"{base_url}/jira-changelog/_mapping", headers=headers, timeout=10)
            if response.status_code == 200:
                mapping_dict = response.json()
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
                logger.error(f"Failed to retrieve updated mapping: {response.status_code}")
        else:
            logger.error("jira-changelog index does not exist")
            
    except Exception as e:
        logger.error(f"Error updating Elasticsearch mapping: {e}")

if __name__ == "__main__":
    main()