#!/usr/bin/env python3
"""
ETL script for populating the JIRA data warehouse with issue history data.
This script can be run on a schedule to regularly sync JIRA data to the database.

Usage:
  python populate_db.py [options]

Options:
  --days DAYS       Number of days of history to fetch (default: 7)
  --max-issues NUM  Maximum number of issues to process (default: no limit)
  --agent NAME      Name of the ETL agent (default: "JiraETLAgent")
  --full-sync       Ignore last sync date and perform a full sync
  --verbose         Enable verbose logging
"""

import logging
import argparse
from datetime import datetime, timedelta
from db_populate import JiraDBPopulator

def setup_logging(verbose=False):
    """Configure logging for the ETL process."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("jira_etl.log"),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from other libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def main():
    """Main entry point for the ETL process."""
    parser = argparse.ArgumentParser(description='Populate JIRA data warehouse')
    parser.add_argument('--days', type=int, default=7, 
                        help='Number of days of history to fetch (default: 7)')
    parser.add_argument('--max-issues', type=int, default=None, 
                        help='Maximum number of issues to process')
    parser.add_argument('--agent', type=str, default='JiraETLAgent', 
                        help='Name of the ETL agent')
    parser.add_argument('--full-sync', action='store_true', 
                        help='Ignore last sync date and perform a full sync')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting JIRA ETL process with agent: {args.agent}")
    
    # Create the populator
    populator = JiraDBPopulator(agent_name=args.agent)
    
    try:
        # Connect to the database
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
        
        # Populate the database
        count = populator.populate_from_jira(
            start_date=start_date,
            end_date=end_date,
            max_issues=args.max_issues
        )
        
        logger.info(f"ETL process completed. Inserted {count} records")
        
        # Get and log database summary
        summary = populator.get_database_summary()
        if summary:
            logger.info(f"Database Summary:")
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
    exit(main())