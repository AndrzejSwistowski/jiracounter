"""
Update Elasticsearch mapping to add @timestamp field and fix components and labels fields.

This script will:
1. Add the @timestamp field to the Elasticsearch mapping
2. Update the components field to be a proper array of text values
3. Update the labels field to be a proper array of keywords
4. Fix the parent_issue and epic_issue fields if needed

Run this script when you need to modify the existing Elasticsearch index mapping.
"""

import logging
import os
import sys
import json
import requests
from datetime import datetime
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("es_mapping_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get Elasticsearch settings from environment variables
ELASTIC_URL = os.environ.get('ELASTIC_URL')
ELASTIC_APIKEY = os.environ.get('ELASTIC_APIKEY')

# Default Elasticsearch connection settings if environment variables not set
ES_HOST = "localhost"
ES_PORT = 9200
ES_USE_SSL = False

# If ELASTIC_URL is provided, parse it to extract host, port, and protocol
if ELASTIC_URL:
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(ELASTIC_URL)
        ES_HOST = parsed_url.hostname or ES_HOST
        ES_PORT = parsed_url.port or ES_PORT
        ES_USE_SSL = parsed_url.scheme == 'https'
        logger.info(f"Using Elasticsearch URL from environment: {ELASTIC_URL}")
    except Exception as e:
        logger.warning(f"Error parsing ELASTIC_URL: {e}. Using defaults.")

# Index names
INDEX_CHANGELOG = "jira-changelog"
TEMP_INDEX = f"{INDEX_CHANGELOG}-temp"

def connect_elasticsearch():
    """Establishes a connection to Elasticsearch."""
    try:
        # Remove trailing slash if present in URL
        if ELASTIC_URL:
            url = ELASTIC_URL.rstrip('/')
        else:
            url = f'{"https" if ES_USE_SSL else "http"}://{ES_HOST}:{ES_PORT}'
            
        # Prepare headers with API key authentication
        headers = {"Content-Type": "application/json"}
        if ELASTIC_APIKEY:
            headers["Authorization"] = f"ApiKey {ELASTIC_APIKEY}"
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
        if ELASTIC_APIKEY:
            connect_args['headers'] = headers
        
        es = Elasticsearch(**connect_args)
        
        return es, url, headers
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        raise

def delete_index(url, headers, index_name):
    """Delete an Elasticsearch index."""
    try:
        # Check if index exists
        response = requests.head(f"{url}/{index_name}", headers=headers)
        if response.status_code == 200:
            logger.info(f"Deleting index {index_name}")
            delete_response = requests.delete(f"{url}/{index_name}", headers=headers)
            if delete_response.status_code >= 200 and delete_response.status_code < 300:
                logger.info(f"Successfully deleted index {index_name}")
                return True
            else:
                logger.error(f"Error deleting index: {delete_response.status_code} - {delete_response.text}")
                return False
        else:
            logger.info(f"Index {index_name} does not exist")
            return True  # Not an error if index doesn't exist
    except Exception as e:
        logger.error(f"Error deleting index {index_name}: {e}")
        return False

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
                    "labels": {"type": "keyword"},  # This will be used as an array
                    "components": {"type": "keyword"},  # Changed from nested to keyword array
                    "projectKey": {"type": "keyword"},
                    "projectName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "authorUserName": {"type": "keyword"},
                    "authorDisplayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
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
        create_response = requests.put(
            f"{url}/{INDEX_CHANGELOG}", 
            headers=headers,
            json=updated_mapping
        )
        
        if create_response.status_code >= 200 and create_response.status_code < 300:
            logger.info(f"Created index {INDEX_CHANGELOG} successfully with updated mapping")
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
        if not delete_index(url, headers, INDEX_CHANGELOG):
            logger.error("Failed to delete existing index. Aborting.")
            return False
        
        # Create a new index with the updated mapping
        if not create_new_index(url, headers):
            logger.error("Failed to create new index with updated mapping. Aborting.")
            return False
        
        logger.info("Successfully updated Elasticsearch mapping. Now run repopulate_es.py to repopulate the index.")
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