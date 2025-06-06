#!/usr/bin/env python3
"""
Enhanced test script to verify the status transition metrics functionality,
including days and period calculations for time in previous status.
"""

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from issue_history_extractor import IssueHistoryExtractor
from jira_field_manager import JiraFieldManager
from issue_data_extractor import IssueDataExtractor
from time_utils import parse_date, to_iso8601

class MockJiraHistory:
    """Mock for JIRA changelog history item."""
    def __init__(self, created, author_name, author_display_name, items):
        self.created = created
        self.author = Mock()
        self.author.name = author_name
        self.author.displayName = author_display_name
        self.items = items

class MockJiraHistoryItem:
    """Mock for JIRA changelog history item field change."""
    def __init__(self, field, from_string, to_string):
        self.field = field
        self.fromString = from_string
        self.toString = to_string

def test_status_transition_metrics_enhanced():
    """Test the enhanced status transition metrics calculation."""
    print("Testing enhanced status transition metrics calculation")
    print("=" * 60)
    
    # Create mocks
    field_manager = Mock(spec=JiraFieldManager)
    data_extractor = Mock(spec=IssueDataExtractor)
    
    # Create extractor instance
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    # Test data: issue with complex workflow including backflow and legacy status names
    creation_date = datetime(2024, 1, 1, 9, 0, 0)  # Jan 1, 2024 at 9:00 AM
    update_date = datetime(2024, 1, 10, 17, 0, 0)  # Jan 10, 2024 at 5:00 PM
    
    # Create mock issue with changelog
    issue = Mock()
    issue.fields.created = creation_date
    issue.fields.updated = update_date
    
    # Create mock changelog entries with status changes
    issue.changelog = Mock()
    issue.changelog.histories = [
        # Day 2: Open → In progress
        MockJiraHistory(
            created=creation_date + timedelta(days=1, hours=1),
            author_name="jdoe",
            author_display_name="John Doe",
            items=[MockJiraHistoryItem(field="status", from_string="Open", to_string="W TRAKCIE")]
        ),
        # Day 3: In progress → In review
        MockJiraHistory(
            created=creation_date + timedelta(days=2, hours=5),
            author_name="jsmith",
            author_display_name="Jane Smith",
            items=[MockJiraHistoryItem(field="status", from_string="W TRAKCIE", to_string="In review")]
        ),
        # Day 4: In review → In progress
        MockJiraHistory(
            created=creation_date + timedelta(days=3, hours=2),
            author_name="jdoe",
            author_display_name="John Doe",
            items=[MockJiraHistoryItem(field="status", from_string="In review", to_string="IN PROGRESS2")]
        ),
        # Day 5: In progress → Testing
        MockJiraHistory(
            created=creation_date + timedelta(days=4, hours=7),
            author_name="jsmith",
            author_display_name="Jane Smith",
            items=[MockJiraHistoryItem(field="status", from_string="IN PROGRESS2", to_string="Testing")]
        ),
        # Day 9: Testing → Done
        MockJiraHistory(
            created=creation_date + timedelta(days=8, hours=6),
            author_name="jdoe",
            author_display_name="John Doe",
            items=[MockJiraHistoryItem(field="status", from_string="Testing", to_string="Done")]
        ),
    ]
    
    # Mock the data extractor to return issue_data
    data_extractor.extract_issue_data.return_value = {
        'key': 'TEST-123',
        'typeName': 'Story',
        'status': 'Done',
        'created': creation_date,
        'updated': update_date,
    }
    
    # Extract the transitions
    transitions = extractor._extract_detailed_status_transitions(issue)
    
    # Display the results
    print(f"Creation date: {to_iso8601(creation_date)}")
    print(f"Update date: {to_iso8601(update_date)}")
    
    print("Status changes:")
    for history in issue.changelog.histories:
        for item in history.items:
            if item.field == "status":
                print(f"  {history.created}: {item.fromString} -> {item.toString}")
    
    print("Detailed transitions:")
    for idx, transition in enumerate(transitions, 1):
        print(f"  {idx}. {transition['from_status']} -> {transition['to_status']}")
        print(f"     Date: {transition['transition_date']}")
        print(f"     Minutes in previous: {transition['minutes_in_previous_status']}")
        print(f"     Days in previous: {transition['days_in_previous_status']}")
        print(f"     Time period: {transition['period_in_previous_status']}")
        print(f"     Forward: {transition['is_forward_transition']}, Backflow: {transition['is_backflow']}")
        print(f"     Author: {transition['author']}")
    
    # Checks
    assert len(transitions) == 5, "Should have 5 status transitions"
    assert all('days_in_previous_status' in t for t in transitions), "All transitions should have days field"
    assert all('period_in_previous_status' in t for t in transitions), "All transitions should have period field"
    
    # Check legacy status name handling
    status_progression = [t['from_status'] + ' -> ' + t['to_status'] for t in transitions]
    assert "In Progress -> In Review" in status_progression, "Legacy status 'W TRAKCIE' should be in transitions"
    assert "In Review -> In Progress" in status_progression, "Legacy status 'IN PROGRESS2' should be in transitions"
    
    # Verify that forward/backflow detection works with legacy status names
    w_trakcie_to_review = transitions[1]  # In Progress -> In Review
    assert w_trakcie_to_review and w_trakcie_to_review['is_forward_transition'], "In Progress -> In Review should be forward"

    review_to_progress2 = transitions[2]  # In Review -> In Progress
    assert review_to_progress2 and review_to_progress2['is_backflow'], "In Review -> In Progress should be backflow"

    print("✅ Enhanced test passed! Status transitions with days and periods are working correctly.")

if __name__ == "__main__":
    test_status_transition_metrics_enhanced()
