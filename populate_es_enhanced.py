#!/usr/bin/env python3
"""
Enhanced ETL script for populating Elasticsearch with JIRA issue history data.
This version includes improved logging to help diagnose issues.
"""

import logging
import argparse
import os
import sys
import traceback
from datetime import datetime, timedelta
from es_populate import JiraElasticsearchPopulator, ELASTIC_URL, ELASTIC_APIKEY, ES_HOST, ES_PORT, ES_USE_SSL

# Create log directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging(verbose=False, log_file=None):
    """Configure logging for the ETL process."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create a unique log filename based on current timestamp if not provided
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOG_DIR, f"jira_etl_es_{timestamp}.log")
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout as well
        ]
    )
    
    # Reduce noise from other libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    
    # Return the log file path so we can inform the user
    return log_file

def main():
    """Main entry point for the ETL process."""
    parser = argparse.ArgumentParser(description='Populate Elasticsearch with JIRA data')
    parser.add_argument('--days', type=int, default=7, 
                        help='Number of days of history to fetch (default: 7)')
    parser.add_argument('--max-issues', type=int, default=None, 
                        help='Maximum number of issues to process')
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
    parser.add_argument('--bulk-size', type=int, default=100,
                        help='Number of records to process in each bulk operation (default: 100)')
    parser.add_argument('--full-sync', action='store_true', 
                        help='Ignore last sync date and perform a full sync')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose logging')
    parser.add_argument('--log-file', type=str, default=None,
                        help='Custom log file path (default: auto-generated in logs directory)')
    
    args = parser.parse_args()
    
    # Set up logging and get the log file path
    log_file_path = setup_logging(args.verbose, args.log_file)
    logger = logging.getLogger(__name__)
    
    # Print information to console so user knows where logs are going
    print(f"\nStarting JIRA to Elasticsearch ETL process")
    print(f"Logs will be written to: {os.path.abspath(log_file_path)}\n")
    
    logger.info(f"Starting JIRA to Elasticsearch ETL process with agent: {args.agent}")
    logger.info(f"Command line arguments: {args}")
    
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
        # Enhanced error logging with full traceback
        logger.error(f"Error during ETL process: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"\nERROR: {e}")
        print(f"See log file for details: {os.path.abspath(log_file_path)}")
        return 1
    finally:
        # Always ensure connection is closed
        if 'populator' in locals():
            populator.close()
    
    print(f"\nETL process completed. See log file for details: {os.path.abspath(log_file_path)}")
    return 0

if __name__ == "__main__":
    exit(main())