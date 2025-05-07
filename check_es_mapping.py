#!/usr/bin/env python
"""
Script to check the Elasticsearch index mapping.
This will show us what fields already exist in the index.
"""

import os
import logging
from elasticsearch import Elasticsearch

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
            
            # Get the index mapping
            mapping = es.indices.get_mapping(index="jira-changelog")
            
            # Print the mapping in a readable format
            logger.info("Index mapping structure:")
            
            # Convert the mapping to a Python dictionary and extract properties
            mapping_dict = mapping.body
            if "jira-changelog" in mapping_dict:
                properties = mapping_dict["jira-changelog"]["mappings"]["properties"]
                logger.info(f"Found {len(properties)} top-level properties in the mapping")
                
                # List all top-level properties
                logger.info("Top-level fields in the index:")
                for field_name in properties.keys():
                    logger.info(f"  - {field_name}")
                
                # Check for specific fields
                if "summary" in properties:
                    logger.info(f"summary field exists with type: {properties['summary'].get('type')}")
                else:
                    logger.warning("summary field does not exist in the index")
                    
                if "labels" in properties:
                    logger.info(f"labels field exists with type: {properties['labels'].get('type')}")
                else:
                    logger.warning("labels field does not exist in the index")
                    
                if "components" in properties:
                    logger.info(f"components field exists with type: {properties['components'].get('type')}")
                else:
                    logger.warning("components field does not exist in the index")
            else:
                logger.warning("Unexpected mapping structure")
            
            # Get a sample document
            result = es.search(
                index="jira-changelog",
                size=1,
                sort=[{"historyDate": {"order": "desc"}}]
            )
            
            if result["hits"]["total"]["value"] > 0:
                sample_doc = result["hits"]["hits"][0]["_source"]
                logger.info("Found a sample document")
                logger.info("Sample document fields:")
                for field_name in sample_doc.keys():
                    logger.info(f"  - {field_name}")
                
                # Check for our specific fields in the sample document
                logger.info("Checking for specific fields in the sample document:")
                logger.info(f"  - summary: {'Present' if 'summary' in sample_doc else 'Missing'}")
                logger.info(f"  - labels: {'Present' if 'labels' in sample_doc else 'Missing'}")
                logger.info(f"  - components: {'Present' if 'components' in sample_doc else 'Missing'}")
            else:
                logger.warning("No documents found in the index")
        else:
            logger.warning("jira-changelog index does not exist")
    
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")

if __name__ == "__main__":
    main()