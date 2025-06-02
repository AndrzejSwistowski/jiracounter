#!/usr/bin/env python3
"""
Test script to verify that status transition detection works correctly with different case variations.
This test specifically addresses the case-sensitive issue in status transition analysis.
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

def test_case_insensitive_status_transitions():
    """Test that status transitions work correctly with different case variations."""
    print("Testing case-insensitive status transition detection")
    print("=" * 60)
    
    # Create mocks
    field_manager = Mock(spec=JiraFieldManager)
    data_extractor = Mock(spec=IssueDataExtractor)
    
    # Create extractor instance
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    creation_date = parse_date("2024-01-01 09:00:00")
    update_date = parse_date("2024-01-05 17:00:00")
    
    # Test with various case combinations that should be detected as transitions
    test_cases = [
        {
            'name': 'Mixed case statuses',
            'history': [
                {
                    'historyDate': parse_date("2024-01-02 10:00:00"),
                    'changes': [{'field': 'status', 'from': 'OPEN', 'to': 'In Progress'}]  # Different cases
                },
                {
                    'historyDate': parse_date("2024-01-03 14:00:00"),
                    'changes': [{'field': 'status', 'from': 'In Progress', 'to': 'IN REVIEW'}]  # Different cases
                },
                {
                    'historyDate': parse_date("2024-01-04 11:00:00"),
                    'changes': [{'field': 'status', 'from': 'IN REVIEW', 'to': 'in progress'}]  # BACKFLOW with different cases
                }
            ],
            'expected_backflows': 1,
            'expected_transitions': 3
        },
        {
            'name': 'All lowercase statuses',
            'history': [
                {
                    'historyDate': parse_date("2024-01-02 10:00:00"),
                    'changes': [{'field': 'status', 'from': 'open', 'to': 'in progress'}]
                },
                {
                    'historyDate': parse_date("2024-01-03 14:00:00"),
                    'changes': [{'field': 'status', 'from': 'in progress', 'to': 'in review'}]
                },
                {
                    'historyDate': parse_date("2024-01-04 11:00:00"),
                    'changes': [{'field': 'status', 'from': 'in review', 'to': 'in progress'}]  # BACKFLOW
                }
            ],
            'expected_backflows': 1,
            'expected_transitions': 3
        },
        {
            'name': 'All uppercase statuses',
            'history': [
                {
                    'historyDate': parse_date("2024-01-02 10:00:00"),
                    'changes': [{'field': 'status', 'from': 'OPEN', 'to': 'IN PROGRESS'}]
                },
                {
                    'historyDate': parse_date("2024-01-03 14:00:00"),
                    'changes': [{'field': 'status', 'from': 'IN PROGRESS', 'to': 'IN REVIEW'}]
                },
                {
                    'historyDate': parse_date("2024-01-04 11:00:00"),
                    'changes': [{'field': 'status', 'from': 'IN REVIEW', 'to': 'IN PROGRESS'}]  # BACKFLOW
                }
            ],
            'expected_backflows': 1,
            'expected_transitions': 3
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print("-" * 40)
        
        result = extractor._calculate_status_transition_metrics(
            test_case['history'], creation_date, update_date
        )
        
        print(f"Status changes:")
        for change in test_case['history']:
            for ch in change['changes']:
                if ch['field'] == 'status':
                    print(f"  {ch['from']} -> {ch['to']}")
        
        print(f"Results:")
        print(f"  Total transitions: {result['total_transitions']} (expected: {test_case['expected_transitions']})")
        print(f"  Backflow count: {result['backflow_count']} (expected: {test_case['expected_backflows']})")
        
        # Verify expectations
        assert result['total_transitions'] == test_case['expected_transitions'], \
            f"Expected {test_case['expected_transitions']} transitions, got {result['total_transitions']}"
        assert result['backflow_count'] == test_case['expected_backflows'], \
            f"Expected {test_case['expected_backflows']} backflows, got {result['backflow_count']}"
        
        # Check specific backflow detection
        backflow_found = False
        for transition in result['status_transitions']:
            if transition['is_backflow']:
                print(f"  Backflow detected: {transition['from_status']} -> {transition['to_status']}")
                backflow_found = True
        
        if test_case['expected_backflows'] > 0:
            assert backflow_found, f"Expected backflow not detected in {test_case['name']}"
        
        print(f"✅ {test_case['name']} passed!")
    
    return True

def test_case_insensitive_categorized_metrics():
    """Test that categorized time metrics work correctly with different case variations."""
    print("\n\nTesting case-insensitive categorized time metrics")
    print("=" * 60)
    
    # Create mocks
    field_manager = Mock(spec=JiraFieldManager)
    data_extractor = Mock(spec=IssueDataExtractor)
    
    # Create extractor instance
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    creation_date = parse_date("2024-01-01 09:00:00")
    update_date = parse_date("2024-01-05 17:00:00")
    
    test_cases = [
        {
            'name': 'Mixed case processing statuses',
            'history': [
                {
                    'historyDate': parse_date("2024-01-02 10:00:00"),
                    'changes': [{'field': 'status', 'from': 'BACKLOG', 'to': 'In Progress'}]  # Should be processing
                },
                {
                    'historyDate': parse_date("2024-01-03 14:00:00"),
                    'changes': [{'field': 'status', 'from': 'In Progress', 'to': 'IN REVIEW'}]  # Should be processing
                },
                {
                    'historyDate': parse_date("2024-01-04 11:00:00"),
                    'changes': [{'field': 'status', 'from': 'IN REVIEW', 'to': 'TESTING'}]  # Should be processing
                }
            ]
        },
        {
            'name': 'All lowercase statuses',
            'history': [
                {
                    'historyDate': parse_date("2024-01-02 10:00:00"),
                    'changes': [{'field': 'status', 'from': 'backlog', 'to': 'in progress'}]
                },
                {
                    'historyDate': parse_date("2024-01-03 14:00:00"),
                    'changes': [{'field': 'status', 'from': 'in progress', 'to': 'in review'}]
                }
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print("-" * 40)
        
        result = extractor._calculate_categorized_time_metrics(
            test_case['history'], creation_date, update_date
        )
        
        print(f"Status changes:")
        for change in test_case['history']:
            for ch in change['changes']:
                if ch['field'] == 'status':
                    print(f"  {ch['from']} -> {ch['to']}")
        
        print(f"Time metrics:")
        print(f"  Backlog minutes: {result['backlog_minutes']}")
        print(f"  Processing minutes: {result['processing_minutes']}")
        print(f"  Waiting minutes: {result['waiting_minutes']}")
        
        # For these test cases, we should have some processing time (since we move to processing statuses)
        # and some backlog time (from the initial period)
        assert result['processing_minutes'] > 0, f"Expected some processing time in {test_case['name']}"
        
        print(f"✅ {test_case['name']} passed!")
    
    return True

if __name__ == "__main__":
    try:
        test_case_insensitive_status_transitions()
        test_case_insensitive_categorized_metrics()
        print("\n🎉 All case-sensitivity tests passed successfully!")
        print("The issue with case-sensitive status comparisons has been fixed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
