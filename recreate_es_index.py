#!/usr/bin/env python3
"""
Script to recreate the Elasticsearch index with the correct mapping.
This is used to fix issues with the components field and other mapping problems.

During development mode, it's preferable to recreate the entire index from scratch
rather than using field mapping updates. This approach ensures:
  - A clean state without potential mapping conflicts
  - Consistent schema across environments
  - Avoidance of mapping incompatibilities that can occur with incremental updates
  - Simpler debugging and testing with known index states

While production systems may require careful incremental mapping updates to avoid
data loss, development environments benefit from the simplicity and reliability
of complete index recreation.

Usage:
  python recreate_es_index.py [options]

Options:
  --agent NAME      Name of the ETL agent (default: "JiraETLAgent")
  --host HOST       Elasticsearch host (default: from ELASTIC_URL env var or "localhost")
  --port PORT       Elasticsearch port (default: from ELASTIC_URL env var or 9200)
  --api-key KEY     Elasticsearch API key (default: from ELASTIC_APIKEY env var)
  --url URL         Complete Elasticsearch URL (default: from ELASTIC_URL env var)
  --confirm         Skip confirmation prompt and proceed with index deletion
  --resync          Perform a full data resync after recreating the index
  --days DAYS       Number of days of data to resync (default: 60)
  --verbose         Enable verbose logging
"""

import logging
import argparse
import os
import sys
from datetime import datetime, timedelta
from es_populate import JiraElasticsearchPopulator, ELASTIC_URL, ELASTIC_APIKEY, ES_HOST, ES_PORT, ES_USE_SSL
from es_populate import INDEX_CHANGELOG, INDEX_SETTINGS
from es_mapping import CHANGELOG_MAPPING, SETTINGS_MAPPING

def setup_logging(verbose=False, log_file="recreate_es_index.log"):
    """Configure logging for the process."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/recreate_es_index_{timestamp}.log"
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from other libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def delete_index(populator, index_name, logger):
    """Delete an Elasticsearch index."""
    try:
        import requests
        
        # Build base URL
        if populator.url:
            base_url = populator.url.rstrip('/')
        else:
            base_url = f'{"https" if populator.use_ssl else "http"}://{populator.host}:{populator.port}'
            
        # Prepare headers with API key authentication
        headers = {"Content-Type": "application/json"}
        if populator.api_key:
            headers["Authorization"] = f"ApiKey {populator.api_key}"
        
        # Delete the index
        logger.info(f"Deleting index {index_name}...")
        delete_response = requests.delete(f"{base_url}/{index_name}", headers=headers)
        
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

def get_last_sync_date_from_settings(populator, logger):
    """Get the last sync date from the settings index before deleting it."""
    try:
        last_sync_date = populator.get_last_sync_date()
        if last_sync_date:
            logger.info(f"Retrieved last sync date before index deletion: {last_sync_date}")
        else:
            logger.warning("No last sync date found in settings")
        return last_sync_date
    except Exception as e:
        logger.error(f"Error getting last sync date: {e}")
        return None

def create_index(populator, index_name, mapping, logger):
    """Create an Elasticsearch index with the specified mapping."""
    try:
        import requests
        import json
        
        # Build base URL
        if populator.url:
            base_url = populator.url.rstrip('/')
        else:
            base_url = f'{"https" if populator.use_ssl else "http"}://{populator.host}:{populator.port}'
            
        # Prepare headers with API key authentication
        headers = {"Content-Type": "application/json"}
        if populator.api_key:
            headers["Authorization"] = f"ApiKey {populator.api_key}"
        
        # Create the index with mapping
        logger.info(f"Creating index {index_name} with explicit mapping...")
        
        # Send PUT request to create the index with mapping
        create_response = requests.put(
            f"{base_url}/{index_name}", 
            headers=headers,
            json=mapping
        )
        
        if create_response.status_code in [200, 201]:
            logger.info(f"Successfully created index {index_name} with explicit mapping")
            return True
        else:
            logger.error(f"Failed to create index {index_name}: {create_response.status_code} - {create_response.text}")
            return False
    except Exception as e:
        logger.error(f"Error creating index {index_name}: {e}")
        return False

def recreate_indices(populator, logger):
    """Create the indices with updated mappings."""
    try:
        logger.info("Creating indices with explicit mappings from es_mapping module")
        
        # Try to create with full mapping first
        result_changelog = create_index(populator, INDEX_CHANGELOG, CHANGELOG_MAPPING, logger)
        
        # If creating with Polish analyzer fails, try a fallback mapping
        if not result_changelog:
            logger.warning("Creating index with Polish analyzer failed. Trying fallback mapping...")
            
            # Create a simplified version of the mapping without custom analyzers
            simplified_mapping = {
                "mappings": CHANGELOG_MAPPING["mappings"]
            }
            
            # Modify text fields to use standard analyzer instead of polish
            for field_name in ["summary", "description_text", "comment_text"]:
                if field_name in simplified_mapping["mappings"]["properties"]:
                    if "fields" in simplified_mapping["mappings"]["properties"][field_name]:
                        # Remove polish analyzer field
                        if "polish" in simplified_mapping["mappings"]["properties"][field_name]["fields"]:
                            del simplified_mapping["mappings"]["properties"][field_name]["fields"]["polish"]
            
            # Try with simplified mapping
            result_changelog = create_index(populator, INDEX_CHANGELOG, simplified_mapping, logger)
            
        if not result_changelog:
            logger.error(f"Failed to create index {INDEX_CHANGELOG}")
            return False
            
        # Create the settings index with the proper mapping
        result_settings = create_index(populator, INDEX_SETTINGS, SETTINGS_MAPPING, logger)
        if not result_settings:
            logger.error(f"Failed to create index {INDEX_SETTINGS}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error creating indices with explicit mappings: {e}")
        return False

def restore_sync_date(populator, last_sync_date, logger):
    """Restore the last sync date in the settings index."""
    if last_sync_date:
        try:
            populator.update_sync_date(last_sync_date)
            logger.info(f"Restored last sync date: {last_sync_date}")
            return True
        except Exception as e:
            logger.error(f"Error restoring last sync date: {e}")
            return False
    return True  # Nothing to restore

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Recreate Elasticsearch index with correct mapping')
    parser.add_argument('--agent', type=str, default='JiraETLAgent', 
                        help='Name of the ETL agent')
    parser.add_argument('--host', type=str, default=ES_HOST,
                        help=f'Elasticsearch host (default: {ES_HOST})')
    parser.add_argument('--port', type=int, default=ES_PORT,
                        help=f'Elasticsearch port (default: {ES_PORT})')
    parser.add_argument('--api-key', type=str, default=ELASTIC_APIKEY,
                        help='Elasticsearch API key (default: from ELASTIC_APIKEY env var)')
    parser.add_argument('--url', type=str, default=ELASTIC_URL,
                        help='Complete Elasticsearch URL (default: from ELASTIC_URL env var)')
    parser.add_argument('--confirm', action='store_true', 
                        help='Skip confirmation prompt and proceed with index deletion')
    parser.add_argument('--resync', action='store_true', 
                        help='Perform a full data resync after recreating the index')
    parser.add_argument('--days', type=int, default=60, 
                        help='Number of days of data to resync (default: 60)')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.verbose)
    
    logger.info("Starting Elasticsearch index recreation process")
    
    # Create the populator
    populator = JiraElasticsearchPopulator(
        agent_name=args.agent,
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        use_ssl=ES_USE_SSL,
        url=args.url
    )
    
    try:
        # Connect to Elasticsearch
        populator.connect()
        
        # Get confirmation for index deletion if not already provided
        if not args.confirm:
            confirmation = input(f"WARNING: This will delete and recreate the '{INDEX_CHANGELOG}' index. All data will be lost. Type 'yes' to continue: ")
            if confirmation.lower() != "yes":
                logger.info("Operation cancelled by user")
                return 0
        
        # Backup the last sync date
        last_sync_date = get_last_sync_date_from_settings(populator, logger)
        
        # Delete the changelog index
        if not delete_index(populator, INDEX_CHANGELOG, logger):
            logger.error("Failed to delete changelog index, aborting")
            return 1
        
        # Delete the settings index
        if not delete_index(populator, INDEX_SETTINGS, logger):
            logger.warning("Failed to delete settings index, continuing anyway")
        
        # Recreate the indices with updated mappings
        if not recreate_indices(populator, logger):
            logger.error("Failed to recreate indices, aborting")
            return 1
        
        # Restore the last sync date
        if not restore_sync_date(populator, last_sync_date, logger):
            logger.warning("Failed to restore last sync date")
        
        # Perform a full resync if requested
        if args.resync:
            logger.info(f"Starting full resync for the last {args.days} days")
            
            # Calculate date range for resync
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            # Perform the resync
            count = populator.populate_from_jira(
                start_date=start_date,
                end_date=end_date,
                bulk_size=100
            )
            
            logger.info(f"Resync completed. Inserted {count} records")
        
        # Get and log database summary
        summary = populator.get_database_summary()
        if summary:
            logger.info(f"Elasticsearch Summary:")
            logger.info(f"Total Records: {summary['total_records']}")
            logger.info(f"Date Range: {summary['oldest_record']} to {summary['newest_record']}")
            logger.info(f"Unique Issues: {summary['unique_issues']}")
            logger.info(f"Unique Projects: {summary['unique_projects']}")
        
        logger.info("Index recreation process completed successfully")
        
    except Exception as e:
        logger.error(f"Error during index recreation: {e}", exc_info=True)
        return 1
    finally:
        # Always ensure connection is closed
        populator.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())