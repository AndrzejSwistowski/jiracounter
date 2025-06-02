#!/usr/bin/env python3
"""
Update Elasticsearch indices for JIRA data.

This script will:
1. Delete existing indices in Elasticsearch
2. Create new indices with updated mappings
3. Populate data for a specified period (default: 7 days)

Usage:
  python update_es_indices.py [options]

Options:
  --days DAYS         Number of days of history to fetch (default: 7)
  --max-issues NUM    Maximum number of issues to process (default: no limit)
  --bulk-size SIZE    Number of records in each bulk operation (default: 100)
  --confirm           Skip confirmation prompt
  --verbose           Enable verbose logging
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
import requests
import json

# Import from existing modules
from es_mapping import CHANGELOG_MAPPING, SETTINGS_MAPPING
from es_populate import JiraElasticsearchPopulator
from logger_utils import setup_logging
from es_utils import delete_index, create_index_with_auto_fallback
import config


def recreate_indices(populator, logger):
    """Recreate Elasticsearch indices using the unified approach."""
    try:
        # Create indices using the unified auto-fallback approach
        success_changelog = create_index_with_auto_fallback(
            url=populator.url,
            api_key=populator.api_key,
            index_name=config.INDEX_CHANGELOG,
            logger=logger
        )
        
        success_settings = create_index_with_auto_fallback(
            url=populator.url,
            api_key=populator.api_key,
            index_name=config.INDEX_SETTINGS,
            logger=logger
        )
        
        return success_changelog and success_settings
    except Exception as e:
        logger.error(f"Error recreating indices: {e}")
        return False


def verify_field_mappings(url, headers, index_name, logger):
    """Verify key fields in the mapping and sample data."""
    try:
        # Check the mapping
        mapping_response = requests.get(f"{url}/{index_name}/_mapping", headers=headers)
        if mapping_response.status_code != 200:
            logger.warning(f"Could not get mapping for {index_name}: {mapping_response.status_code}")
            return False
            
        # Get a sample document to verify data
        sample_query = {
            "size": 1,
            "query": {"match_all": {}}
        }
        
        sample_response = requests.post(
            f"{url}/{index_name}/_search", 
            headers=headers,
            json=sample_query
        )
        
        if sample_response.status_code != 200:
            logger.warning(f"Could not get sample data from {index_name}: {sample_response.status_code}")
            return False
            
        sample_data = sample_response.json()
        if sample_data["hits"]["total"]["value"] == 0:
            logger.warning(f"No documents found in {index_name}")
            return False
            
        # Get the first document
        doc = sample_data["hits"]["hits"][0]["_source"]
        
        # Log the content of key fields
        fields_to_check = ["description_text", "comment_text", "status_change_date", "created", "updated"]
        logger.info("Sample document field verification:")
        
        for field in fields_to_check:
            if field in doc:
                value = doc[field]
                if value:
                    logger.info(f"  ✓ Field '{field}' has value: {value[:50]}..." if isinstance(value, str) and len(value) > 50 else f"  ✓ Field '{field}' has value: {value}")
                else:
                    logger.warning(f"  ✗ Field '{field}' exists but is empty")
            else:
                logger.warning(f"  ✗ Field '{field}' is missing from document")
                
        return True
    except Exception as e:
        logger.error(f"Error verifying field mappings: {e}")
        return False


def main():
    """Main entry point for updating Elasticsearch indices."""
    parser = argparse.ArgumentParser(description='Update Elasticsearch indices for JIRA data')
    parser.add_argument('--days', type=int, default=7, 
                        help='Number of days of history to fetch (default: 7)')
    parser.add_argument('--max-issues', type=int, default=None, 
                        help='Maximum number of issues to process')
    parser.add_argument('--bulk-size', type=int, default=100,
                        help='Number of records in each bulk operation (default: 100)')
    parser.add_argument('--confirm', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(
        verbose=args.verbose,
        log_prefix="update_es_indices"
    )
    
    logger.info("Starting Elasticsearch index update process")
    
    try:
        # Connect to Elasticsearch using config
        es_config = config.get_elasticsearch_config()
        
        # Build the connection URL
        if es_config['url']:
            url = es_config['url'].rstrip('/')
        else:
            url = f"http://{es_config['host']}:{es_config['port']}"
        
        # Prepare headers for HTTP requests
        headers = {"Content-Type": "application/json"}
        if es_config['api_key']:
            headers["Authorization"] = f"ApiKey {es_config['api_key']}"
            logger.info("Using API key authentication")
        
        # Test the connection
        response = requests.get(f"{url}/_cluster/health", headers=headers, timeout=10)
        if response.status_code != 200:
            raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code}")
        
        logger.info("Successfully connected to Elasticsearch")
        
        # Log that we're using expanded text field limits
        logger.info("Using expanded text field limits for description and comment fields (up to 32KB)")
        logger.info("Added comment text extraction for better searchability")
        
        # Before deleting, log the current mapping for reference if needed
        try:
            current_mapping_response = requests.get(f"{url}/{config.INDEX_CHANGELOG}/_mapping", headers=headers)
            if current_mapping_response.status_code == 200:
                logger.debug("Current mapping before update retrieved successfully")
        except Exception as e:
            logger.debug(f"Could not retrieve current mapping: {e}")
        
        # Get confirmation for index deletion if not already provided
        if not args.confirm:
            confirmation = input(f"WARNING: This will delete indices '{config.INDEX_CHANGELOG}' and '{config.INDEX_SETTINGS}'. "
                               f"All data will be lost. Type 'yes' to continue: ")
            if confirmation.lower() != "yes":
                logger.info("Index update cancelled by user")
                return 0
        
        # Delete the indices
        indices_to_delete = [config.INDEX_CHANGELOG, config.INDEX_SETTINGS]
        for index_name in indices_to_delete:
            delete_result = delete_index(url=url, api_key=es_config['api_key'], index_name=index_name, logger=logger)
            if not delete_result:
                logger.error(f"Failed to delete index {index_name}, aborting")
                return 1
        
        # Create the Elasticsearch populator for recreating indices
        populator = JiraElasticsearchPopulator(
            agent_name="JiraETLAgent",
            host=es_config['host'],
            port=es_config['port'],
            api_key=es_config['api_key'],
            use_ssl=es_config['use_ssl'],
            url=es_config['url']
        )
        
        # Connect the populator
        populator.connect()
        
        # Recreate the indices with updated mappings
        if not recreate_indices(populator, logger):
            logger.error("Failed to recreate indices, aborting")
            return 1
        
        logger.info("Indices recreated successfully with updated mappings")
        
        # Determine date range for data population
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        logger.info(f"Populating data for the last {args.days} days")
        
        # Populate Elasticsearch
        count = populator.populate_from_jira(
            start_date=start_date,
            end_date=end_date,
            max_issues=args.max_issues,
            bulk_size=args.bulk_size
        )
        
        logger.info(f"Data population completed. Inserted {count} records")
        
        # Verify field mappings and data
        if count > 0:
            logger.info("Verifying field mappings and data...")
            verify_field_mappings(url, headers, config.INDEX_CHANGELOG, logger)
        
        # Get and log database summary
        summary = populator.get_database_summary()
        if summary:
            logger.info(f"Elasticsearch Summary:")
            logger.info(f"Total Records: {summary['total_records']}")
            logger.info(f"Date Range: {summary['oldest_record']} to {summary['newest_record']}")
            logger.info(f"Unique Issues: {summary['unique_issues']}")
            logger.info(f"Unique Projects: {summary['unique_projects']}")
        
    except Exception as e:
        logger.error(f"Error during index update process: {e}", exc_info=True)
        return 1
    finally:
        # Always ensure connection is closed
        try:
            if 'populator' in locals():
                populator.close()
        except:
            pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
