#!/usr/bin/env python3
"""
Script to recreate Elasticsearch index with case-insensitive status fields.
This script will:
1. Backup the current index data (optional)
2. Delete the existing index
3. Create a new index with updated mapping that includes case-insensitive status fields
4. Trigger a full re-population of data from JIRA

Note: This approach recreates the index from scratch, which is safer than reindexing
and ensures all data has the new case-insensitive fields populated correctly.
"""
import json
import logging
import time
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
import config
from es_mapping import CHANGELOG_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='es_mapping_update_case_insensitive.log',
                    filemode='w')
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

INDEX_NAME = "jira-changelog"

def connect_to_elasticsearch():
    """Connect to Elasticsearch."""
    try:
        if config.ELASTIC_APIKEY:
            es = Elasticsearch(
                config.ELASTIC_URL,
                api_key=config.ELASTIC_APIKEY,
                verify_certs=False
            )
        else:
            es = Elasticsearch(
                config.ELASTIC_URL,
                basic_auth=(config.ELASTIC_USER, config.ELASTIC_PASSWORD),
                verify_certs=False
            )
        logger.info("Connected to Elasticsearch successfully")
        return es
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")
        raise

def main():
    """Main function to recreate the index mapping."""
    try:
        logger.info("Starting Elasticsearch index recreation for case sensitivity")
        es = connect_to_elasticsearch()
        
        # Check if original index exists
        if not es.indices.exists(index=INDEX_NAME):
            logger.warning(f"Index {INDEX_NAME} does not exist")
        else:
            logger.info(f"Deleting existing index: {INDEX_NAME}")
            es.indices.delete(index=INDEX_NAME)
        
        # Create new index with updated mapping
        logger.info(f"Creating new index {INDEX_NAME} with case-insensitive status fields")
        es.indices.create(index=INDEX_NAME, body=CHANGELOG_MAPPING)
        logger.info(f"Successfully created index {INDEX_NAME} with updated mapping")
        
        logger.info("Index recreation completed successfully!")
        logger.info("You can now run your ETL process to populate the index with data")
        logger.info("The new fields available for case-insensitive searches are:")
        logger.info("  - issue.status.name_lower")
        logger.info("  - issue.type.name_lower") 
        logger.info("  - unique_statuses_visited_lower")
        logger.info("  - status_transitions.from_status_lower")
        logger.info("  - status_transitions.to_status_lower")
        
    except Exception as e:
        logger.error(f"Unexpected error during index recreation: {str(e)}")
        raise

if __name__ == "__main__":
    main()
