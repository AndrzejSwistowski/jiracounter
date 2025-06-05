#!/usr/bin/env python3
"""
Test script for working time calculation functions.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_utils import (
    calculate_working_minutes_between,
    calculate_working_minutes_since_date,
    is_polish_holiday,
    is_working_day,
    parse_date
)

def test_basic_working_minutes():
    """Test basic working minutes calculation."""
    print("=== Testing Basic Working Minutes Calculation ===")
    
    # Test 1: Same day, partial hours
    start = "2025-05-27 10:00:00"  # Tuesday 10 AM
    end = "2025-05-27 14:00:00"    # Tuesday 2 PM
    minutes = calculate_working_minutes_between(start, end)
    print(f"Same day (10 AM - 2 PM): {minutes} minutes (expected: 240)")
    
    # Test 2: Full working day
    start = "2025-05-27 09:00:00"  # Tuesday 9 AM
    end = "2025-05-27 17:00:00"    # Tuesday 5 PM
    minutes = calculate_working_minutes_between(start, end)
    print(f"Full working day (9 AM - 5 PM): {minutes} minutes (expected: 480)")
    
    # Test 3: Multiple days
    start = "2025-05-27 09:00:00"  # Tuesday 9 AM
    end = "2025-05-29 17:00:00"    # Thursday 5 PM
    minutes = calculate_working_minutes_between(start, end)
    print(f"Three working days (Tue-Thu): {minutes} minutes (expected: 1440)")

def test_weekend_exclusion():
    """Test weekend exclusion."""
    print("\n=== Testing Weekend Exclusion ===")
    
    # Test Friday to Monday (should skip weekend)
    start = "2025-05-23 15:00:00"  # Friday 3 PM
    end = "2025-05-26 11:00:00"    # Monday 11 AM
    minutes = calculate_working_minutes_between(start, end)
    print(f"Friday 3PM to Monday 11AM: {minutes} minutes (expected: 320 - 2h Fri + 2h Mon)")

def test_polish_holidays():
    """Test Polish holiday exclusion."""
    print("\n=== Testing Polish Holiday Detection ===")
    
    # Test New Year's Day 2025
    new_year = parse_date("2025-01-01")
    is_holiday = is_polish_holiday(new_year)
    is_work_day = is_working_day(new_year)
    print(f"New Year's Day 2025: Holiday={is_holiday}, Working Day={is_work_day}")
    
    # Test Christmas 2024
    christmas = parse_date("2024-12-25")
    is_holiday = is_polish_holiday(christmas)
    is_work_day = is_working_day(christmas)
    print(f"Christmas 2024: Holiday={is_holiday}, Working Day={is_work_day}")
    
    # Test regular working day
    regular_day = parse_date("2025-05-27")  # Tuesday
    is_holiday = is_polish_holiday(regular_day)
    is_work_day = is_working_day(regular_day)
    print(f"Regular Tuesday 2025-05-27: Holiday={is_holiday}, Working Day={is_work_day}")

def test_edge_cases():
    """Test edge cases."""
    print("\n=== Testing Edge Cases ===")
    
    # Test before work hours - NEW BEHAVIOR: same day counts all minutes
    start = "2025-05-27 07:00:00"  # 7 AM
    end = "2025-05-27 10:00:00"    # 10 AM
    minutes = calculate_working_minutes_between(start, end)
    print(f"7 AM - 10 AM (same day - all minutes counted): {minutes} minutes (expected: 180)")
    
    # Test after work hours - NEW BEHAVIOR: same day counts all minutes
    start = "2025-05-27 16:00:00"  # 4 PM
    end = "2025-05-27 19:00:00"    # 7 PM
    minutes = calculate_working_minutes_between(start, end)
    print(f"4 PM - 7 PM (same day - all minutes counted): {minutes} minutes (expected: 180)")
    
    # Test completely outside work hours - NEW BEHAVIOR: same day counts all minutes
    start = "2025-05-27 19:00:00"  # 7 PM
    end = "2025-05-27 21:00:00"    # 9 PM
    minutes = calculate_working_minutes_between(start, end)
    print(f"7 PM - 9 PM (same day - all minutes counted): {minutes} minutes (expected: 120)")

def test_since_date():
    """Test calculation since a specific date."""
    print("\n=== Testing Since Date Calculation ===")
    
    # Test from yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
    minutes = calculate_working_minutes_since_date(yesterday)
    print(f"Minutes since yesterday 10 AM: {minutes}")

if __name__ == "__main__":
    print("Testing Working Time Calculation Functions")
    print("=" * 50)
    
    test_basic_working_minutes()
    test_weekend_exclusion()
    test_polish_holidays()
    test_edge_cases()
    test_since_date()
    
    print("\n" + "=" * 50)
    print("Test completed!")
