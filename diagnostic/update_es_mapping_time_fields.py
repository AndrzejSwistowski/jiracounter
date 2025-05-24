"""
Update Elasticsearch mapping to add aggregated time-based fields:
- workingDaysFromCreation: Number of working days since issue was created
- workingDaysInStatus: Number of working days issue has been in current status
- working_days_from_move_at_point: Number of working days since issue had its first status change

This script will:
1. Connect to Elasticsearch
2. Update the Elasticsearch mapping with the new fields
3. Delete and recreate the index with the updated mapping

Run this script when you need to modify the existing Elasticsearch index mapping.
"""

import logging
import os
import sys
import json
import requests
from datetime import datetime
from elasticsearch import Elasticsearch

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from es_utils import delete_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("es_mapping_time_fields.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Index names from config
TEMP_INDEX = f"{config.INDEX_CHANGELOG}-temp"

def connect_elasticsearch():
    """Establishes a connection to Elasticsearch."""
    try:
        es_config = config.get_elasticsearch_config()
        
        # Build the connection URL
        if es_config['url']:
            url = es_config['url'].rstrip('/')
        else:
            url = f'{"https" if es_config["use_ssl"] else "http"}://{es_config["host"]}:{es_config["port"]}'
            
        # Prepare headers with API key authentication
        headers = {"Content-Type": "application/json"}
        if es_config['api_key']:
            headers["Authorization"] = f"ApiKey {es_config['api_key']}"
            logger.info("Using API key authentication")
        
        # Test the connection by requesting cluster health
        response = requests.get(f"{url}/_cluster/health", headers=headers)
        
        if response.status_code != 200:
            raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code} - {response.text}")
            
        health_data = response.json()
        logger.info(f"Successfully connected to Elasticsearch cluster: {health_data['cluster_name']} / Status: {health_data['status']}")
        
        # Create the Elasticsearch client instance with the same connection params
        connect_args = {'hosts': [url]}
        
        # Add API key authentication if provided
        if es_config['api_key']:
            connect_args['headers'] = headers
        
        es = Elasticsearch(**connect_args)
        
        return es, url, headers
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        raise

# This function has been moved to es_utils.py
# It is now imported at the top of the file

def create_new_index(url, headers):
    """Create a new index with the updated mapping."""
    try:
        # Define an updated mapping for changelog entries with fixed field types
        updated_mapping = {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},  # Add @timestamp field for Kibana
                    "historyId": {"type": "keyword"},
                    "historyDate": {"type": "date"},
                    "factType": {"type": "integer"},
                    "issueId": {"type": "keyword"},
                    "issueKey": {"type": "keyword"},
                    "typeName": {"type": "keyword"},
                    "statusName": {"type": "keyword"},
                    "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "labels": {"type": "keyword"},  # Used as an array
                    "components": {"type": "keyword"},  # Used as an array
                    "projectKey": {"type": "keyword"},
                    "projectName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "authorUserName": {"type": "keyword"},
                    "authorDisplayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    
                    # New aggregated time-based fields
                    "workingDaysFromCreation": {"type": "float"},  # Working days since issue was created
                    "workingDaysInStatus": {"type": "float"},  # Working days in current status
                    "working_days_from_move_at_point": {"type": "float"},  # Working days since first status change
                    
                    "issue": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "key": {"type": "keyword"},
                            "type": {
                                "properties": {
                                    "name": {"type": "keyword"}
                                }
                            },
                            "status": {
                                "properties": {
                                    "name": {"type": "keyword"}
                                }
                            }
                        }
                    },
                    "project": {
                        "properties": {
                            "key": {"type": "keyword"},
                            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "author": {
                        "properties": {
                            "username": {"type": "keyword"},
                            "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "assignee": {
                        "properties": {
                            "username": {"type": "keyword"},
                            "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "reporter": {
                        "properties": {
                            "username": {"type": "keyword"},
                            "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "allocation": {
                        "properties": {
                            "code": {"type": "keyword"},
                            "name": {"type": "keyword"}
                        }
                    },
                    "parentKey": {"type": "keyword"},
                    "changes": {
                        "properties": {
                            "field": {"type": "keyword"},
                            "from": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
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
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        # Create the new index with the updated mapping
        create_response = requests.put(            f"{url}/{config.INDEX_CHANGELOG}", 
            headers=headers,
            json=updated_mapping
        )
        
        if create_response.status_code >= 200 and create_response.status_code < 300:
            logger.info(f"Created index {config.INDEX_CHANGELOG} successfully with updated mapping")
            return True
        else:
            logger.error(f"Error creating index: {create_response.status_code} - {create_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating new index: {e}")
        return False

def main():
    try:
        # Connect to Elasticsearch
        es, url, headers = connect_elasticsearch()
          # Delete the existing index
        if not delete_index(url=url, api_key=None, index_name=config.INDEX_CHANGELOG, logger=logger):
            logger.error("Failed to delete existing index. Aborting.")
            return False
        
        # Create a new index with the updated mapping
        if not create_new_index(url, headers):
            logger.error("Failed to create new index with updated mapping. Aborting.")
            return False
        
        logger.info("Successfully updated Elasticsearch mapping with new time-based fields.")
        logger.info("Now run repopulate_es.py to repopulate the index with the time calculations.")
        return True
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return False
    finally:
        # Clean up
        try:
            es.close()
            logger.info("Elasticsearch connection closed")
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)