#!/usr/bin/env python3
"""
Script to fully repopulate the Elasticsearch database with all historical Jira data.
This will fetch data from the beginning of your Jira instance's history.
"""

import logging
import argparse
import sys
from datetime import datetime, timedelta
from es_populate import JiraElasticsearchPopulator

def setup_logging(verbose=True):
    """Configure logging for the repopulation process."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("jira_full_repopulate.log"),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from other libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)

def main():
    """Main entry point for the full repopulation process."""
    parser = argparse.ArgumentParser(description='Fully repopulate Elasticsearch with all historical Jira data')
    parser.add_argument('--days', type=int, default=3650,  # Default to ~10 years
                        help='Number of days of history to fetch (default: 3650 - about 10 years)')
    parser.add_argument('--batch-size', type=int, default=30, 
                        help='Number of days to process in each batch (default: 30)')
    parser.add_argument('--max-issues', type=int, default=None, 
                        help='Maximum number of issues to process per batch (for testing)')
    parser.add_argument('--agent', type=str, default='JiraETLAgent', 
                        help='Name of the ETL agent')
    parser.add_argument('--bulk-size', type=int, default=100,
                        help='Number of records to process in each bulk operation (default: 100)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be done without actually importing data')
    parser.add_argument('--continue-on-error', action='store_true',
                        help='Continue processing other batches if one fails')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(verbose=True)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting full repopulation of Elasticsearch with historical Jira data")
    logger.info(f"Will process approximately {args.days} days of history in batches of {args.batch_size} days")
    
    # Create the populator
    populator = JiraElasticsearchPopulator(agent_name=args.agent)
    
    try:
        # Connect to Elasticsearch
        populator.connect()
        
        
        # Calculate the total date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        logger.info(f"Full date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Process data in batches
        current_start = start_date
        batch_number = 1
        total_records = 0
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=args.batch_size), end_date)
            
            logger.info(f"Processing batch {batch_number}: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")
            
            if args.dry_run:
                logger.info(f"DRY RUN: Would import data from {current_start} to {current_end}")
                count = 0
            else:
                try:
                    # Populate Elasticsearch with data from the current batch
                    count = populator.populate_from_jira(
                        start_date=current_start,
                        end_date=current_end,
                        max_issues=args.max_issues,
                        bulk_size=args.bulk_size
                    )
                    
                    logger.info(f"Batch {batch_number} completed: Inserted {count} records")
                    total_records += count
                    
                except Exception as e:
                    logger.error(f"Error processing batch {batch_number}: {e}", exc_info=True)
                    if not args.continue_on_error:
                        logger.error("Stopping due to error. Use --continue-on-error to process remaining batches.")
                        return 1
            
            # Move to the next batch
            current_start = current_end
            batch_number += 1
        
        logger.info(f"Repopulation process completed. Total records inserted: {total_records}")
        
        if not args.dry_run:
            # Get and log database summary
            summary = populator.get_database_summary(days=args.days)
            if summary:
                logger.info(f"Elasticsearch Summary:")
                logger.info(f"Total Records: {summary['total_records']}")
                logger.info(f"Date Range: {summary['oldest_record']} to {summary['newest_record']}")
                logger.info(f"Unique Issues: {summary['unique_issues']}")
                logger.info(f"Unique Projects: {summary['unique_projects']}")
        
    except Exception as e:
        logger.error(f"Error during repopulation process: {e}", exc_info=True)
        return 1
    finally:
        # Always ensure connection is closed
        populator.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())