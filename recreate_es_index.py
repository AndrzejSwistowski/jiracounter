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
from es_populate import JiraElasticsearchPopulator
import config
from logger_utils import setup_logging
from es_utils import delete_index, create_index_with_auto_fallback

# This function has been moved to es_utils.py
# It is now imported at the top of the file

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

# This function has been moved to es_utils.py
# It is now imported at the top of the file

def recreate_indices(populator, logger):
    """Create the indices with updated mappings using unified approach."""
    try:
        logger.info("Creating indices with automatic fallback mappings")
        
        # Use the new unified function for changelog index
        result_changelog = create_index_with_auto_fallback(
            populator=populator, 
            index_name=config.INDEX_CHANGELOG, 
            logger=logger
        )
        
        if not result_changelog:
            logger.error(f"Failed to create index {config.INDEX_CHANGELOG}")
            return False
            
        # Use the new unified function for settings index  
        result_settings = create_index_with_auto_fallback(
            populator=populator, 
            index_name=config.INDEX_SETTINGS, 
            logger=logger
        )
        
        if not result_settings:
            logger.error(f"Failed to create index {config.INDEX_SETTINGS}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error creating indices with unified approach: {e}")
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
    es_config = config.get_elasticsearch_config()
    
    parser = argparse.ArgumentParser(description='Recreate Elasticsearch index with correct mapping')
    parser.add_argument('--agent', type=str, default='JiraETLAgent', 
                        help='Name of the ETL agent')
    parser.add_argument('--host', type=str, default=es_config['host'],
                        help=f'Elasticsearch host (default: {es_config["host"]})')
    parser.add_argument('--port', type=int, default=es_config['port'],
                        help=f'Elasticsearch port (default: {es_config["port"]})')
    parser.add_argument('--api-key', type=str, default=es_config['api_key'],
                        help='Elasticsearch API key (default: from ELASTIC_APIKEY env var)')
    parser.add_argument('--url', type=str, default=es_config['url'],
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
    logger = setup_logging(
        verbose=args.verbose,
        log_prefix="recreate_es_index"
    )
    
    logger.info("Starting Elasticsearch index recreation process")
    
    # Create the populator
    populator = JiraElasticsearchPopulator(
        agent_name=args.agent,
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        use_ssl=es_config['use_ssl'],
        url=args.url
    )
    
    try:
        # Connect to Elasticsearch
        populator.connect()
        
        # Get confirmation for index deletion if not already provided
        if not args.confirm:
            confirmation = input(f"WARNING: This will delete and recreate the '{config.INDEX_CHANGELOG}' index. All data will be lost. Type 'yes' to continue: ")
            if confirmation.lower() != "yes":
                logger.info("Operation cancelled by user")
                return 0
        
        # Backup the last sync date
        last_sync_date = get_last_sync_date_from_settings(populator, logger)
          # Delete the changelog index
        if not delete_index(populator=populator, index_name=config.INDEX_CHANGELOG, logger=logger):
            logger.error("Failed to delete changelog index, aborting")
            return 1
        
        # Delete the settings index
        if not delete_index(populator=populator, index_name=config.INDEX_SETTINGS, logger=logger):
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