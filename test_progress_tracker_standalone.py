#!/usr/bin/env python3
"""
Test script for using the new ProgressTracker class directly.
This script demonstrates how to use the ProgressTracker without requiring es_populate.py.
"""

import time
import logging
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

if __name__ == "__main__":
    # Run the standalone test
    test_progress_tracker()
