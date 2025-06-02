#!/usr/bin/env python3
"""
Script to verify the case-insensitive status field mappings in Elasticsearch.
"""
import json
import logging
from elasticsearch import Elasticsearch
import config

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check Elasticsearch index mappings for case-insensitive fields."""
    # Connect to Elasticsearch
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
        
        try:
            # Get mappings for jira-changelog index
            mappings = es.indices.get_mapping(index="jira-changelog")
            properties = mappings["jira-changelog"]["mappings"]["properties"]
            
            print("\n=== Case-Insensitive Status Field Mappings ===")
            
            # Check issue.status fields
            if "issue" in properties and "properties" in properties["issue"]:
                issue_props = properties["issue"]["properties"]
                if "status" in issue_props and "properties" in issue_props["status"]:
                    status_props = issue_props["status"]["properties"]
                    print(f"issue.status.name: {json.dumps(status_props.get('name', {}), indent=2)}")
                    print(f"issue.status.name_lower: {json.dumps(status_props.get('name_lower', {}), indent=2)}")
                
                # Check issue.type fields
                if "type" in issue_props and "properties" in issue_props["type"]:
                    type_props = issue_props["type"]["properties"]
                    print(f"issue.type.name: {json.dumps(type_props.get('name', {}), indent=2)}")
                    print(f"issue.type.name_lower: {json.dumps(type_props.get('name_lower', {}), indent=2)}")
            
            # Check unique_statuses_visited fields
            print(f"unique_statuses_visited: {json.dumps(properties.get('unique_statuses_visited', {}), indent=2)}")
            print(f"unique_statuses_visited_lower: {json.dumps(properties.get('unique_statuses_visited_lower', {}), indent=2)}")
            
            # Check status_transitions fields
            if "status_transitions" in properties and "properties" in properties["status_transitions"]:
                trans_props = properties["status_transitions"]["properties"]
                print(f"status_transitions.from_status: {json.dumps(trans_props.get('from_status', {}), indent=2)}")
                print(f"status_transitions.from_status_lower: {json.dumps(trans_props.get('from_status_lower', {}), indent=2)}")
                print(f"status_transitions.to_status: {json.dumps(trans_props.get('to_status', {}), indent=2)}")
                print(f"status_transitions.to_status_lower: {json.dumps(trans_props.get('to_status_lower', {}), indent=2)}")
            
            # Check normalizers in settings
            settings = es.indices.get_settings(index="jira-changelog")
            analysis = settings.get("jira-changelog", {}).get("settings", {}).get("index", {}).get("analysis", {})
            print(f"\nNormalizers: {json.dumps(analysis.get('normalizer', {}), indent=2)}")
            
        except Exception as e:
            logger.error(f"Error retrieving data from Elasticsearch: {str(e)}")
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")

if __name__ == "__main__":
    main()
