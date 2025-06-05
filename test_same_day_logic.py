#!/usr/bin/env python3
"""
Test script specifically for the new same-day logic in calculate_working_minutes_between.
This tests the modification where same-day times are counted regardless of working hours.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_utils import calculate_working_minutes_between, parse_date

def test_same_day_within_working_hours():
    """Test same-day calculations within working hours."""
    print("=== Same Day - Within Working Hours ===")
    
    test_cases = [
        ("2025-05-27 10:00:00", "2025-05-27 14:00:00", 240, "Morning to afternoon"),
        ("2025-05-27 09:00:00", "2025-05-27 17:00:00", 480, "Full working day"),
        ("2025-05-27 09:00:00", "2025-05-27 09:30:00", 30, "30 minutes"),
        ("2025-05-27 16:30:00", "2025-05-27 17:00:00", 30, "Last 30 minutes"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_same_day_outside_working_hours():
    """Test same-day calculations outside working hours - NEW BEHAVIOR."""
    print("\n=== Same Day - Outside Working Hours (NEW BEHAVIOR) ===")
    
    test_cases = [
        ("2025-05-27 18:00:00", "2025-05-27 19:30:00", 90, "Evening (after work)"),
        ("2025-05-27 07:00:00", "2025-05-27 08:00:00", 60, "Early morning (before work)"),
        ("2025-05-27 19:00:00", "2025-05-27 21:00:00", 120, "Night time"),
        ("2025-05-27 06:00:00", "2025-05-27 07:30:00", 90, "Very early morning"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_same_day_crossing_working_hours():
    """Test same-day calculations that cross working hour boundaries."""
    print("\n=== Same Day - Crossing Working Hours ===")
    
    test_cases = [
        ("2025-05-27 08:00:00", "2025-05-27 10:00:00", 120, "Before work to during work"),
        ("2025-05-27 16:00:00", "2025-05-27 18:00:00", 120, "During work to after work"),
        ("2025-05-27 07:00:00", "2025-05-27 19:00:00", 720, "All day (before to after work)"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_same_day_on_weekends():
    """Test same-day calculations on weekends."""
    print("\n=== Same Day - Weekends (NEW BEHAVIOR) ===")
    
    test_cases = [
        ("2025-05-24 10:00:00", "2025-05-24 14:00:00", 240, "Saturday afternoon"),
        ("2025-05-25 09:00:00", "2025-05-25 17:00:00", 480, "Sunday full day"),
        ("2025-05-24 18:00:00", "2025-05-24 20:00:00", 120, "Saturday evening"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_same_day_on_holidays():
    """Test same-day calculations on Polish holidays."""
    print("\n=== Same Day - Polish Holidays (NEW BEHAVIOR) ===")
    
    test_cases = [
        ("2025-01-01 10:00:00", "2025-01-01 14:00:00", 240, "New Year's Day"),
        ("2025-12-25 09:00:00", "2025-12-25 17:00:00", 480, "Christmas Day"),
        ("2025-05-01 15:00:00", "2025-05-01 18:00:00", 180, "Labour Day evening"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_multi_day_behavior_unchanged():
    """Test that multi-day calculations still work as before."""
    print("\n=== Multi-Day - Behavior Should Be Unchanged ===")
    
    test_cases = [
        ("2025-05-27 09:00:00", "2025-05-28 17:00:00", 960, "Two working days"),
        ("2025-05-27 18:00:00", "2025-05-28 10:00:00", 60, "Evening to next morning"),
        ("2025-05-23 15:00:00", "2025-05-26 11:00:00", 240, "Friday afternoon to Monday morning"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_edge_cases():
    """Test edge cases for same-day logic."""
    print("\n=== Edge Cases ===")
    
    test_cases = [
        ("2025-05-27 10:00:00", "2025-05-27 10:00:00", 0, "Same time"),
        ("2025-05-27 10:00:00", "2025-05-27 10:01:00", 1, "One minute"),
        ("2025-05-27 23:59:00", "2025-05-27 23:59:59", 0, "59 seconds (rounds to 0)"),
    ]
    
    for start, end, expected, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

if __name__ == "__main__":
    print("Testing Same-Day Logic in calculate_working_minutes_between")
    print("=" * 70)
    print("This tests the new behavior where same-day times are counted")
    print("regardless of working hours.")
    print()
    
    test_same_day_within_working_hours()
    test_same_day_outside_working_hours()
    test_same_day_crossing_working_hours()
    test_same_day_on_weekends()
    test_same_day_on_holidays()
    test_multi_day_behavior_unchanged()
    test_edge_cases()
    
    print("\n" + "=" * 70)
    print("Same-day logic testing completed!")
    print("\nThe modification ensures that when start_date and end_date are")
    print("on the same day, ALL minutes between them are counted, regardless")
    print("of working hours, weekends, or holidays.")
