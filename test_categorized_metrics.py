#!/usr/bin/env python3
"""
Test script to verify the categorized time metrics functionality.
"""

import sys
import os
from unittest.mock import Mock
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from issue_history_extractor import IssueHistoryExtractor
from jira_field_manager import JiraFieldManager
from issue_data_extractor import IssueDataExtractor
from time_utils import parse_date, to_iso8601

def test_categorized_time_metrics():
    """Test the categorized time metrics calculation."""
    print("Testing categorized time metrics calculation")
    print("=" * 60)
    
    # Create mocks
    field_manager = Mock(spec=JiraFieldManager)
    data_extractor = Mock(spec=IssueDataExtractor)
    
    # Create extractor instance
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    # Test data: issue created on Monday, moved through different statuses
    creation_date = parse_date("2024-01-01 09:00:00")  # Monday 9 AM
    update_date = parse_date("2024-01-05 17:00:00")    # Friday 5 PM
    
    # Status change history: Backlog -> In progress -> In review -> testing -> Done
    status_change_history = [
        {
            'historyDate': parse_date("2024-01-02 10:00:00"),  # Tuesday 10 AM
            'changes': [{'field': 'status', 'from': 'Backlog', 'to': 'In progress'}]
        },
        {
            'historyDate': parse_date("2024-01-03 14:00:00"),  # Wednesday 2 PM
            'changes': [{'field': 'status', 'from': 'In progress', 'to': 'In review'}]
        },
        {
            'historyDate': parse_date("2024-01-04 11:00:00"),  # Thursday 11 AM
            'changes': [{'field': 'status', 'from': 'In review', 'to': 'testing'}]
        },
        {
            'historyDate': parse_date("2024-01-05 16:00:00"),  # Friday 4 PM
            'changes': [{'field': 'status', 'from': 'testing', 'to': 'Done'}]
        }
    ]
    
    # Calculate categorized metrics
    result = extractor._calculate_categorized_time_metrics(
        status_change_history, creation_date, update_date
    )
    
    print(f"Creation date: {to_iso8601(creation_date)}")
    print(f"Update date: {to_iso8601(update_date)}")
    print(f"Status changes:")
    for change in status_change_history:
        for ch in change['changes']:
            if ch['field'] == 'status':
                print(f"  {to_iso8601(change['historyDate'])}: {ch['from']} -> {ch['to']}")
    
    print(f"\nCategorized time metrics:")
    print(f"  Backlog minutes: {result['backlog_minutes']}")
    print(f"  Processing minutes: {result['processing_minutes']}")  
    print(f"  Waiting minutes: {result['waiting_minutes']}")
    
    # Convert to hours for easier interpretation
    print(f"\nIn hours:")
    print(f"  Backlog hours: {result['backlog_minutes'] / 60:.1f}")
    print(f"  Processing hours: {result['processing_minutes'] / 60:.1f}")
    print(f"  Waiting hours: {result['waiting_minutes'] / 60:.1f}")
    
    # Verify some basic expectations
    assert result['backlog_minutes'] > 0, "Should have time in backlog"
    assert result['processing_minutes'] > 0, "Should have time in processing"
    assert result['waiting_minutes'] == 0, "Should have no waiting time (all statuses were processing or backlog)"
    
    print(f"\n✅ Test passed! Categorized time metrics are working correctly.")
    return True

if __name__ == "__main__":
    try:
        test_categorized_time_metrics()
        print("\n🎉 All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
