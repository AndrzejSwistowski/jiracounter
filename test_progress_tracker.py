#!/usr/bin/env python3
"""
Test script for the new ProgressTracker implementation.
This script runs a small ETL job to verify the ProgressTracker functionality.
"""

import sys
import time
from datetime import datetime, timedelta
import logging
from es_populate import JiraElasticsearchPopulator
from progress_tracker import ProgressTracker
from logger_utils import setup_logging

def test_progress_tracker():
    """Test the progress tracker with a simple simulation."""
    # Set up logging
    logger = setup_logging(verbose=True, log_prefix="progress_tracker_test")
    
    # Create a tracker
    tracker = ProgressTracker(logger=logger, name="test_tracker")
    
    # Simulate processing items
    total_items = 100
    logger.info(f"Starting test with {total_items} items")
    
    tracker.reset()
    for i in range(1, total_items + 1):
        # Process item (simulate with sleep)
        time.sleep(0.05)
        
        # Update progress
        tracker.update(increment=1, total=total_items, interval=10)
    
    # Log final progress
    tracker.update(increment=0, total=total_items, force_log=True)
    
    logger.info(f"Test completed. Average rate: {tracker.items_per_second:.2f} items/sec")

def test_es_populator():
    """Test the ProgressTracker integration with JiraElasticsearchPopulator."""
    # Set up logging
    logger = setup_logging(verbose=True, log_prefix="es_populator_test")
    
    logger.info("Testing ProgressTracker integration with JiraElasticsearchPopulator")
    
    # Create populator
    populator = JiraElasticsearchPopulator(agent_name="TestAgent")
    
    try:
        # Connect to Elasticsearch
        populator.connect()
        
        # Small date range for testing
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        # Only process a few issues for testing
        max_issues = 10
        
        logger.info(f"Running test ETL job from {start_date} to {end_date}")
        
        # Run the populate job
        count = populator.populate_from_jira(
            start_date=start_date,
            end_date=end_date,
            max_issues=max_issues,
            bulk_size=2  # Small bulk size to see more progress updates
        )
        
        logger.info(f"Test ETL job completed. Processed {count} records.")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        populator.close()

if __name__ == "__main__":
    # Run the standalone test first
    test_progress_tracker()
    
    # Uncomment to test with real Elasticsearch
    # test_es_populator()
