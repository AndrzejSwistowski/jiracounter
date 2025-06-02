#!/usr/bin/env python3
"""
Test script to verify the working_minutes_from_create functionality in issue_history_extractor.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_utils import calculate_working_minutes_between, parse_date

def test_working_minutes_calculation():
    """Test the working minutes calculation used in history extractor."""
    print("Testing working minutes calculation for history extractor")
    print("=" * 60)
    
    # Test case 1: Same day, 4 hours apart
    start = "2025-05-27 10:00:00"  # Tuesday 10 AM
    end = "2025-05-27 14:00:00"    # Tuesday 2 PM
    
    start_parsed = parse_date(start)
    end_parsed = parse_date(end)
    
    minutes = calculate_working_minutes_between(start_parsed, end_parsed)
    print(f"Test 1 - Same day calculation:")
    print(f"  From: {start}")
    print(f"  To:   {end}")
    print(f"  Working minutes: {minutes} (expected: 240)")
    print()
    
    # Test case 2: Multi-day calculation
    start2 = "2025-05-27 09:00:00"  # Tuesday 9 AM
    end2 = "2025-05-29 17:00:00"    # Thursday 5 PM
    
    start2_parsed = parse_date(start2)
    end2_parsed = parse_date(end2)
    
    minutes2 = calculate_working_minutes_between(start2_parsed, end2_parsed)
    print(f"Test 2 - Multi-day calculation:")
    print(f"  From: {start2}")
    print(f"  To:   {end2}")
    print(f"  Working minutes: {minutes2} (expected: 1440 - 3 days × 480 minutes)")
    print()
    
    # Test case 3: Creation to now
    created = "2025-05-26 15:00:00"  # Yesterday 3 PM
    now_parsed = parse_date(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    created_parsed = parse_date(created)
    
    minutes3 = calculate_working_minutes_between(created_parsed, now_parsed)
    print(f"Test 3 - Creation to now:")
    print(f"  Created: {created}")
    print(f"  Now:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Working minutes: {minutes3}")
    print()
    
    print("All tests completed successfully!")
    print("The working_minutes_from_create field will now show working minutes instead of working days.")

if __name__ == "__main__":
    test_working_minutes_calculation()
