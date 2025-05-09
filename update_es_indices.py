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
from elasticsearch import Elasticsearch

# Import from existing modules
from reset_es_sync_date import connect_elasticsearch, ELASTIC_URL, ELASTIC_APIKEY
from es_mapping import CHANGELOG_MAPPING, SETTINGS_MAPPING
from populate_es import setup_logging, recreate_indices
from es_populate import JiraElasticsearchPopulator, INDEX_CHANGELOG, INDEX_SETTINGS, ES_HOST, ES_PORT, ES_USE_SSL

def delete_index(url, headers, index_name, logger):
    """Delete an Elasticsearch index."""
    try:
        # Delete the index
        logger.info(f"Deleting index {index_name}...")
        delete_response = requests.delete(f"{url}/{index_name}", headers=headers)
        
        if delete_response.status_code == 200:
            logger.info(f"Successfully deleted index {index_name}")
            return True
        elif delete_response.status_code == 404:
            logger.info(f"Index {index_name} does not exist, nothing to delete")
            return True
        else:
            logger.error(f"Failed to delete index {index_name}: {delete_response.status_code} - {delete_response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting index {index_name}: {e}")
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
    logger = setup_logging(args.verbose)
    
    logger.info("Starting Elasticsearch index update process")
    
    try:
        # Connect to Elasticsearch
        es, url, headers = connect_elasticsearch()
        
        # Log that we're using expanded text field limits
        logger.info("Using expanded text field limits for description and comment fields (up to 32KB)")
        logger.info("Added comment text extraction for better searchability")
        
        # Before deleting, log the current mapping for reference if needed
        try:
            current_mapping_response = requests.get(f"{url}/{INDEX_CHANGELOG}/_mapping", headers=headers)
            if current_mapping_response.status_code == 200:
                logger.debug("Current mapping before update retrieved successfully")
        except Exception as e:
            logger.debug(f"Could not retrieve current mapping: {e}")
        
        # Get confirmation for index deletion if not already provided
        if not args.confirm:
            confirmation = input(f"WARNING: This will delete indices '{INDEX_CHANGELOG}' and '{INDEX_SETTINGS}'. "
                               f"All data will be lost. Type 'yes' to continue: ")
            if confirmation.lower() != "yes":
                logger.info("Index update cancelled by user")
                return 0
        
        # Delete the indices
        indices_to_delete = [INDEX_CHANGELOG, INDEX_SETTINGS]
        for index_name in indices_to_delete:
            delete_result = delete_index(url, headers, index_name, logger)
            if not delete_result:
                logger.error(f"Failed to delete index {index_name}, aborting")
                return 1
        
        # Create the Elasticsearch populator for recreating indices
        populator = JiraElasticsearchPopulator(
            agent_name="JiraETLAgent",
            host=ES_HOST,
            port=ES_PORT,
            api_key=ELASTIC_APIKEY,
            use_ssl=ES_USE_SSL,
            url=ELASTIC_URL
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
            es.close()
            populator.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
