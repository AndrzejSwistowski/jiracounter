#!/usr/bin/env python3
"""
ETL script for populating Elasticsearch with JIRA issue history data.
This script can be run on a schedule to regularly sync JIRA data to Elasticsearch.

Usage:
  python populate_es.py [options]

Options:
  --days DAYS         Number of days of history to fetch (default: 7)
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

# Track progress globally
progress_count = 0
start_time = None

def setup_logging(verbose=False):
    """Configure logging for the ETL process."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/jira_etl_es_{timestamp}.log"
    
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
    
    logger = logging.getLogger(__name__)
    logger.info(f"Log file: {log_filename}")
    
    return logger

def log_progress(logger, current, total=None, interval=30):
    """Log progress at regular intervals to prevent log file from growing too large."""
    global progress_count, start_time
    
    progress_count += current
    
    # Only initialize start_time on first call
    if start_time is None:
        start_time = time.time()
        
    current_time = time.time()
    elapsed = current_time - start_time
    
    # Calculate items per second
    rate = progress_count / elapsed if elapsed > 0 else 0
    
    # Format as HH:MM:SS
    elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
    
    # Log with percentage if total is known
    if total:
        percentage = (progress_count / total) * 100
        logger.info(f"Progress: {progress_count}/{total} ({percentage:.1f}%) | Rate: {rate:.2f} items/sec | Elapsed: {elapsed_str}")
    else:
        logger.info(f"Progress: {progress_count} items | Rate: {rate:.2f} items/sec | Elapsed: {elapsed_str}")
    
    # Estimate remaining time if total is known
    if total and rate > 0:
        remaining_items = total - progress_count
        estimated_seconds = remaining_items / rate
        remaining_str = time.strftime('%H:%M:%S', time.gmtime(estimated_seconds))
        logger.info(f"Estimated time remaining: {remaining_str}")
        
    return progress_count

def delete_index(populator, index_name, logger):
    """Delete an Elasticsearch index."""
    try:
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
    parser.add_argument('--days', type=int, default=1, 
                        help='Number of days of history to fetch (default: 1)')
    parser.add_argument('--max-issues', type=int, default=None, 
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
    logger = setup_logging(args.verbose)
    
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
            logger.info("Index recreated successfully, proceeding with full sync")
          # Determine date range
        end_date = datetime.now()
        
        if args.full_sync:
            # For full sync, use the specified days
            start_date = end_date - timedelta(days=args.days)
            logger.info(f"Performing full sync for the last {args.days} days")
        else:
            # For incremental sync, get the last sync date
            start_date = populator.get_last_sync_date()
            
            if start_date is None:
                # If no previous sync, default to specified days
                start_date = end_date - timedelta(days=args.days)
                logger.info(f"No previous sync found, using last {args.days} days")
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