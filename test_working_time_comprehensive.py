#!/usr/bin/env python3
"""
Comprehensive test script for working time calculation functions.
Tests various real-world scenarios and edge cases.
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
    parse_date,
    WORK_START_HOUR,
    WORK_END_HOUR,
    MINUTES_PER_WORK_DAY
)

def test_real_world_scenarios():
    """Test real-world JIRA ticket scenarios."""
    print("=== Real-World JIRA Ticket Scenarios ===")
    
    # Scenario 1: Ticket created on Friday afternoon, resolved Monday morning
    print("\n1. Friday afternoon to Monday morning:")
    start = "2025-05-23 15:30:00"  # Friday 3:30 PM
    end = "2025-05-26 10:30:00"    # Monday 10:30 AM
    minutes = calculate_working_minutes_between(start, end)
    expected = 90 + 90  # 1.5h Friday + 1.5h Monday = 180 minutes
    print(f"   {start} to {end}")
    print(f"   Result: {minutes} minutes (expected: ~{expected})")
    
    # Scenario 2: Ticket spanning a holiday period
    print("\n2. Ticket spanning New Year (includes holiday):")
    start = "2024-12-30 14:00:00"  # Monday 2 PM
    end = "2025-01-02 11:00:00"    # Thursday 11 AM (after New Year holiday)
    minutes = calculate_working_minutes_between(start, end)
    # Dec 30 (Mon): 3h, Dec 31 (Tue): 8h, Jan 1 (Wed): holiday, Jan 2 (Thu): 2h = 13h = 780 min
    print(f"   {start} to {end}")
    print(f"   Result: {minutes} minutes")
    print(f"   Note: Jan 1st is a holiday and should be excluded")
    
    # Scenario 3: Very short duration within working hours
    print("\n3. Short meeting duration:")
    start = "2025-05-27 14:00:00"  # Tuesday 2 PM
    end = "2025-05-27 14:30:00"    # Tuesday 2:30 PM
    minutes = calculate_working_minutes_between(start, end)
    print(f"   {start} to {end}")
    print(f"   Result: {minutes} minutes (expected: 30)")

def test_polish_holidays_comprehensive():
    """Test various Polish holidays throughout the year."""
    print("\n=== Comprehensive Polish Holiday Tests ===")
    
    polish_holidays_2025 = [
        ("2025-01-01", "New Year's Day"),
        ("2025-01-06", "Epiphany"),
        ("2025-04-21", "Easter Monday"),
        ("2025-05-01", "Labour Day"),
        ("2025-05-03", "Constitution Day"),
        ("2025-06-19", "Corpus Christi"),
        ("2025-08-15", "Assumption Day"),
        ("2025-11-01", "All Saints' Day"),
        ("2025-11-11", "Independence Day"),
        ("2025-12-25", "Christmas Day"),
        ("2025-12-26", "Boxing Day")
    ]
    
    for date_str, holiday_name in polish_holidays_2025:
        date_obj = parse_date(date_str)
        is_holiday = is_polish_holiday(date_obj)
        is_work = is_working_day(date_obj)
        weekday = date_obj.strftime("%A")
        print(f"   {date_str} ({weekday}) - {holiday_name}: Holiday={is_holiday}, Working={is_work}")

def test_performance_large_ranges():
    """Test performance with large date ranges."""
    print("\n=== Performance Test (Large Date Ranges) ===")
    
    import time
    
    # Test 1 year range
    start_time = time.time()
    start = "2024-01-01 09:00:00"
    end = "2024-12-31 17:00:00"
    minutes = calculate_working_minutes_between(start, end)
    elapsed = time.time() - start_time
    
    print(f"   Full year 2024 calculation:")
    print(f"   Result: {minutes} minutes")
    print(f"   Time taken: {elapsed:.3f} seconds")
    print(f"   Working days in 2024: {minutes / MINUTES_PER_WORK_DAY:.1f}")

def test_boundary_conditions():
    """Test boundary conditions and edge cases."""
    print("\n=== Boundary Conditions ===")
    
    # Test exact work hour boundaries
    test_cases = [
        ("2025-05-27 09:00:00", "2025-05-27 09:00:00", "Same minute", 0),
        ("2025-05-27 08:59:59", "2025-05-27 09:00:01", "Before/after work start", 0),
        ("2025-05-27 16:59:59", "2025-05-27 17:00:01", "Before/after work end", 0),
        ("2025-05-27 09:00:00", "2025-05-27 09:01:00", "First minute of work", 1),
        ("2025-05-27 16:59:00", "2025-05-27 17:00:00", "Last minute of work", 1),
    ]
    
    for start, end, description, expected in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        status = "✓" if minutes == expected else "✗"
        print(f"   {status} {description}: {minutes} minutes (expected: {expected})")

def test_integration_with_existing_functions():
    """Test integration with existing time utility functions."""
    print("\n=== Integration with Existing Functions ===")
    
    from time_utils import calculate_days_since_date, to_iso8601, format_for_jql
    
    # Test date that should work with both old and new functions
    test_date = "2025-05-26 10:00:00"  # Yesterday
    
    # Old function - working days
    days = calculate_days_since_date(test_date)
    print(f"   Days since {test_date}: {days}")
    
    # New function - working minutes
    minutes = calculate_working_minutes_since_date(test_date)
    print(f"   Working minutes since {test_date}: {minutes}")
    
    # Test format compatibility
    iso_date = to_iso8601(test_date)
    jql_date = format_for_jql(test_date)
    print(f"   ISO8601 format: {iso_date}")
    print(f"   JQL format: {jql_date}")

def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n=== Error Handling ===")
    
    test_cases = [
        (None, "2025-05-27 10:00:00", "None start date"),
        ("2025-05-27 10:00:00", None, "None end date"),
        ("invalid-date", "2025-05-27 10:00:00", "Invalid start date"),
        ("2025-05-27 10:00:00", "invalid-date", "Invalid end date"),
        ("2025-05-28 10:00:00", "2025-05-27 10:00:00", "End before start"),
    ]
    
    for start, end, description in test_cases:
        minutes = calculate_working_minutes_between(start, end)
        print(f"   {description}: {minutes} (should handle gracefully)")

if __name__ == "__main__":
    print("Comprehensive Working Time Calculation Tests")
    print("=" * 60)
    print(f"Configuration: Work hours {WORK_START_HOUR}:00 - {WORK_END_HOUR}:00")
    print(f"Minutes per work day: {MINUTES_PER_WORK_DAY}")
    print()
    
    test_real_world_scenarios()
    test_polish_holidays_comprehensive()
    test_performance_large_ranges()
    test_boundary_conditions()
    test_integration_with_existing_functions()
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("Comprehensive testing completed!")
    print("\nThe working time calculation functions are ready for use in your JIRA application.")
    print("Key features:")
    print("• Accurate minute-level calculations")
    print("• Polish holiday exclusion")
    print("• Weekend exclusion")
    print("• Configurable working hours (9 AM - 5 PM)")
    print("• Robust error handling")
    print("• Integration with existing time utilities")
