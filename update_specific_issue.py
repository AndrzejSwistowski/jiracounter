#!/usr/bin/env python3
"""
Script to update a specific Jira issue in Elasticsearch.
This is useful for testing and verifying individual issue data.
"""

import logging
import argparse
import sys
from datetime import datetime, timedelta
from es_populate import JiraElasticsearchPopulator
from jiraservice import JiraService
from logger_utils import setup_logging

def main():
    """Main entry point for updating a specific issue."""
    parser = argparse.ArgumentParser(description='Update a specific Jira issue in Elasticsearch')
    parser.add_argument('--issue_key', type=str, default='UTR-448', help='The Jira issue key to update (e.g., POL-396)')
    parser.add_argument('--agent', type=str, default='JiraETLAgent', 
                        help='Name of the ETL agent (default: JiraETLAgent)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be done without actually importing data')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(
        verbose=True,
        log_prefix="jira_issue_update",
        use_timestamp=True
    )
    
    logger.info(f"Starting update for specific issue: {args.issue_key}")
    
    # Create the populator and jira service
    populator = JiraElasticsearchPopulator(agent_name=args.agent)
    jira_service = JiraService()
    
    try:
        # Connect to Elasticsearch
        populator.connect()

        if args.dry_run:
            logger.info(f"DRY RUN: Would update issue {args.issue_key}")
            return 0
        
        # Get the specific issue data with changelog
        logger.info(f"Fetching detailed data with changelog for issue {args.issue_key}")
        issue_record = jira_service.get_issue_changelog(args.issue_key)
        
        if not issue_record:
            logger.error(f"Could not find issue {args.issue_key}")
            return 1
            
        logger.info(f"Successfully retrieved issue data for {args.issue_key}")
        
        # Insert or update the issue in Elasticsearch
        logger.info(f"Inserting/updating issue {args.issue_key} in Elasticsearch")
        inserted_count = populator.bulk_insert_issue_history([issue_record], force_override=True)
        
        if inserted_count > 0:
            logger.info(f"Successfully inserted/updated {inserted_count} records for issue {args.issue_key}")
        else:
            logger.error(f"Failed to insert/update issue {args.issue_key}")
            return 1
        
    except Exception as e:
        logger.error(f"Error during issue update: {e}", exc_info=True)
        return 1
    finally:
        # Always ensure connection is closed
        populator.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
