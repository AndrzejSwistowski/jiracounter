#!/usr/bin/env python3
"""
Test script for the format_working_minutes_to_text function.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_utils import format_working_minutes_to_text, MINUTES_PER_WORK_DAY

def test_format_working_minutes():
    """Test the format_working_minutes_to_text function with various inputs."""
    print("Testing format_working_minutes_to_text function")
    print("=" * 50)
    
    # Test cases: (minutes, expected_description)
    test_cases = [
        (0, "0 minutes"),
        (15, "15 minutes"),
        (60, "1 hour"),
        (90, "1 hour 30 minutes"),
        (480, "1 working day (8 hours)"),
        (540, "1 working day 1 hour"),
        (720, "1 working day 4 hours"),
        (960, "2 working days"),
        (2400, "1 working week (5 days)"),
        (2880, "1 working week 1 working day"),
        (3360, "1 working week 2 working days"),
        (4800, "2 working weeks"),
        (7200, "3 working weeks"),
        (12000, "5 working weeks"),
        (14400, "6 working weeks"),        (None, "None input"),
        (-10, "Negative input"),
    ]
    
    for minutes, description in test_cases:
        result = format_working_minutes_to_text(minutes)
        minutes_str = str(minutes) if minutes is not None else "None"
        print(f"{description:25} ({minutes_str:>5} min) -> {result}")
    
    print(f"\nWorking day definition: {MINUTES_PER_WORK_DAY} minutes (8 hours)")
    print("Working week definition: 2400 minutes (5 working days)")

if __name__ == "__main__":
    test_format_working_minutes()
