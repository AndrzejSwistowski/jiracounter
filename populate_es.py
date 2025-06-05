#!/usr/bin/env python3
"""
ETL script for populating Elasticsearch with JIRA issue history data.
This script can be run on a schedule to regularly sync JIRA data to Elasticsearch.

Usage:
  python populate_es.py [options]

Options:
  --max-issues NUM    Maximum number of issues to process (default: no limit)
  --agent NAME        Name of the ETL agent (default: "JiraETLAgent")
  --host HOST         Elasticsearch host (default: from ELASTIC_URL env var or "localhost")
  --port PORT         Elasticsearch port (default: from ELASTIC_URL env var or 9200)
  --api-key KEY       Elasticsearch API key (default: from ELASTIC_APIKEY env var)
  --url URL           Complete Elasticsearch URL (default: from ELASTIC_URL env var)
  --bulk-size SIZE    Number of records to process in each bulk operation (default: 100)
  --full-sync         Ignore last sync date and perform a full sync
  --recreate-index    Delete and recreate the Elasticsearch index with updated mappings
  --confirm           Skip confirmation prompt when recreating index
  --verbose           Enable verbose logging
"""

import logging
import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from es_populate import JiraElasticsearchPopulator
import config
from es_mapping import CHANGELOG_MAPPING, SETTINGS_MAPPING
import requests
from logger_utils import setup_logging
from progress_tracker import ProgressTracker
from es_utils import delete_index

# For backward compatibility - delegates to ProgressTracker
def log_progress(logger, current, total=None, interval=30):
    """
    Legacy function that delegates to ProgressTracker.
    
    This function is maintained for backward compatibility.
    New code should use the ProgressTracker class directly.
    """
    # Get or create a singleton tracker for backward compatibility
    if not hasattr(log_progress, '_tracker'):
        log_progress._tracker = ProgressTracker(logger=logger, name="etl_progress")
        
    return log_progress._tracker.update(increment=current, total=total, interval=interval)

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

def recreate_indices(populator, logger):
    """Create the indices with updated mappings."""
    try:
        result = populator.create_indices()
        if result:
            logger.info("Successfully created indices with updated mappings")
        else:
            logger.error("Failed to create indices with updated mappings")
        return result
    except Exception as e:
        logger.error(f"Error creating indices: {e}")
        return False

def main():
    """Main entry point for the ETL process."""
    es_config = config.get_elasticsearch_config()
    
    parser = argparse.ArgumentParser(description='Populate Elasticsearch with JIRA data')
    parser.add_argument('--max-issues', type=int, default=1000, 
                        help='Maximum number of issues to process')
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
    parser.add_argument('--bulk-size', type=int, default=100,
                        help='Number of records to process in each bulk operation (default: 100)')
    parser.add_argument('--full-sync', action='store_true', 
                        help='Ignore last sync date and perform a full sync')
    parser.add_argument('--recreate-index', action='store_true',
                        help='Delete and recreate the Elasticsearch index with updated mappings')
    parser.add_argument('--confirm', action='store_true',
                        help='Skip confirmation prompt when recreating index')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
      # Set up logging
    logger = setup_logging(
        verbose=args.verbose,
        log_prefix="jira_etl_es"
    )
    
    logger.info(f"Starting JIRA to Elasticsearch ETL process with agent: {args.agent}")
    
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
        
        # Handle index recreation if requested
        if args.recreate_index:
            # Get confirmation for index deletion if not already provided
            if not args.confirm:
                confirmation = input(f"WARNING: This will delete and recreate the '{config.INDEX_CHANGELOG}' index. "
                                   f"All data will be lost. Type 'yes' to continue: ")
                if confirmation.lower() != "yes":
                    logger.info("Index recreation cancelled by user")
                    return 0
            
            # Backup the last sync date
            last_sync_date = get_last_sync_date_from_settings(populator, logger)
            
            # Delete the changelog index
            if not delete_index(populator, config.INDEX_CHANGELOG, logger):
                logger.error("Failed to delete changelog index, aborting")
                return 1
              # Recreate the indices with updated mappings
            if not recreate_indices(populator, logger):
                logger.error("Failed to recreate indices, aborting")
                return 1
            
            # Restore the last sync date
            if not restore_sync_date(populator, last_sync_date, logger):
                logger.warning("Failed to restore last sync date")
                
            # Force full sync when recreating index
            args.full_sync = True
            logger.info("Index recreated successfully, proceeding with full sync")          # Determine date range - ensure timezone consistency
        from utils import APP_TIMEZONE
        end_date = datetime.now(APP_TIMEZONE)
        
        if args.full_sync:
            # For full sync, default to 7 days if no previous sync date
            default_days = 7
            start_date = end_date - timedelta(days=default_days)
            logger.info(f"Performing full sync for the last {default_days} days")
        else:
            # For incremental sync, get the last sync date
            start_date = populator.get_last_sync_date()
            
            if start_date is None:
                # If no previous sync, default to 7 days
                default_days = 7
                start_date = end_date - timedelta(days=default_days)
                logger.info(f"No previous sync found, using last {default_days} days")
            else:
                logger.info(f"Performing incremental sync from last sync date: {start_date}")

        # Populate Elasticsearch
        logger.info(f"Starting ETL process from {start_date} to {end_date}")
        count = populator.populate_from_jira(
            start_date=start_date,
            end_date=end_date,
            max_issues=args.max_issues,
            bulk_size=args.bulk_size
        )
        
        logger.info(f"ETL process completed. Inserted {count} records")
        
        # Get and log database summary
        summary = populator.get_database_summary()
        if summary:
            logger.info(f"Elasticsearch Summary:")
            logger.info(f"Total Records: {summary['total_records']}")
            logger.info(f"Date Range: {summary['oldest_record']} to {summary['newest_record']}")
            logger.info(f"Unique Issues: {summary['unique_issues']}")
            logger.info(f"Unique Projects: {summary['unique_projects']}")
        
    except Exception as e:
        logger.error(f"Error during ETL process: {e}", exc_info=True)
        return 1
    finally:
        # Always ensure connection is closed
        populator.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())