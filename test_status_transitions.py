#!/usr/bin/env python3
"""
Test script to verify the status transition metrics functionality.
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

def test_status_transition_metrics():
    """Test the status transition metrics calculation."""
    print("Testing status transition metrics calculation")
    print("=" * 60)
    
    # Create mocks
    field_manager = Mock(spec=JiraFieldManager)
    data_extractor = Mock(spec=IssueDataExtractor)
    
    # Create extractor instance
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    # Test data: issue with complex workflow including backflow
    creation_date = parse_date("2024-01-01 09:00:00")  # Monday 9 AM
    update_date = parse_date("2024-01-08 17:00:00")    # Next Monday 5 PM
    
    # Status change history: Open -> In progress -> In review -> In progress (backflow) -> testing -> Done
    status_change_history = [
        {
            'historyDate': parse_date("2024-01-02 10:00:00"),  # Tuesday 10 AM
            'changes': [{'field': 'status', 'from': 'Open', 'to': 'In progress'}]
        },
        {
            'historyDate': parse_date("2024-01-03 14:00:00"),  # Wednesday 2 PM
            'changes': [{'field': 'status', 'from': 'In progress', 'to': 'In review'}]
        },
        {
            'historyDate': parse_date("2024-01-04 11:00:00"),  # Thursday 11 AM (BACKFLOW)
            'changes': [{'field': 'status', 'from': 'In review', 'to': 'In progress'}]
        },
        {
            'historyDate': parse_date("2024-01-05 16:00:00"),  # Friday 4 PM
            'changes': [{'field': 'status', 'from': 'In progress', 'to': 'testing'}]
        },
        {
            'historyDate': parse_date("2024-01-08 15:00:00"),  # Monday 3 PM
            'changes': [{'field': 'status', 'from': 'testing', 'to': 'Done'}]
        }
    ]
    
    # Calculate transition metrics
    result = extractor._calculate_status_transition_metrics(
        status_change_history, creation_date, update_date
    )
    
    print(f"Creation date: {to_iso8601(creation_date)}")
    print(f"Update date: {to_iso8601(update_date)}")
    print(f"Status changes:")
    for change in status_change_history:
        for ch in change['changes']:
            if ch['field'] == 'status':
                print(f"  {to_iso8601(change['historyDate'])}: {ch['from']} -> {ch['to']}")
    
    print(f"\nStatus transition metrics:")
    print(f"  Current status: {result['current_status']}")
    print(f"  Previous status: {result['previous_status']}")
    print(f"  Total transitions: {result['total_transitions']}")
    print(f"  Backflow count: {result['backflow_count']}")
    print(f"  Unique statuses visited: {result['unique_statuses_visited']}")
    print(f"  Current status minutes: {result['current_status_minutes']}")
    
    print(f"\nDetailed transitions:")
    for i, transition in enumerate(result['status_transitions'], 1):
        print(f"  {i}. {transition['from_status']} -> {transition['to_status']}")
        print(f"     Date: {transition['transition_date']}")
        print(f"     Minutes in previous: {transition['minutes_in_previous_status']}")
        print(f"     Forward: {transition['is_forward_transition']}, Backflow: {transition['is_backflow']}")
        print()
    
    # Verify expectations
    assert result['current_status'] == 'Done', f"Expected current status 'Done', got '{result['current_status']}'"
    assert result['previous_status'] == 'testing', f"Expected previous status 'testing', got '{result['previous_status']}'"
    assert result['total_transitions'] == 5, f"Expected 5 transitions, got {result['total_transitions']}"
    assert result['backflow_count'] == 1, f"Expected 1 backflow, got {result['backflow_count']}"
    assert len(result['unique_statuses_visited']) == 5, f"Expected 5 unique statuses, got {len(result['unique_statuses_visited'])}"
    
    # Check for the backflow transition
    backflow_found = False
    for transition in result['status_transitions']:
        if transition['from_status'] == 'In review' and transition['to_status'] == 'In progress':
            assert transition['is_backflow'] == True, "Expected backflow detection for In review -> In progress"
            backflow_found = True
            break
    assert backflow_found, "Backflow transition not found"
    
    print(f"✅ Test passed! Status transition metrics are working correctly.")
    return True

def test_no_status_changes():
    """Test transition metrics when there are no status changes."""
    print("\nTesting transition metrics with no status changes")
    print("=" * 60)
    
    # Create mocks
    field_manager = Mock(spec=JiraFieldManager)
    data_extractor = Mock(spec=IssueDataExtractor)
    
    # Create extractor instance
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    creation_date = parse_date("2024-01-01 09:00:00")
    update_date = parse_date("2024-01-05 17:00:00")
    
    # No status changes
    status_change_history = []
    
    result = extractor._calculate_status_transition_metrics(
        status_change_history, creation_date, update_date
    )
    
    print(f"Result for no status changes:")
    print(f"  Current status: {result['current_status']}")
    print(f"  Previous status: {result['previous_status']}")
    print(f"  Total transitions: {result['total_transitions']}")
    print(f"  Backflow count: {result['backflow_count']}")
    print(f"  Unique statuses visited: {result['unique_statuses_visited']}")
    
    # Verify expectations
    assert result['current_status'] == 'Backlog', "Expected default status 'Backlog'"
    assert result['previous_status'] is None, "Expected no previous status"
    assert result['total_transitions'] == 0, "Expected 0 transitions"
    assert result['backflow_count'] == 0, "Expected 0 backflows"
    assert result['unique_statuses_visited'] == ['Backlog'], "Expected only 'Backlog' status"
    
    print(f"✅ Test passed! No status changes handled correctly.")
    return True

if __name__ == "__main__":
    try:
        test_status_transition_metrics()
        test_no_status_changes()
        print("\n🎉 All status transition tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
