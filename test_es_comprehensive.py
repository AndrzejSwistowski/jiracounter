#!/usr/bin/env python3
"""
Test script to verify the ES document formatter works with issue records.
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from es_document_formatter import ElasticsearchDocumentFormatter
from es_populate import JiraElasticsearchPopulator

def test_issue_formatting():
    """Test formatting of issue records for ES."""
    print("Testing issue record formatting...")
    
    # Create a sample issue record
    sample_record = {
        'issue_data': {
            'id': '12345',
            'key': 'TEST-123',
            'type': 'Story',
            'status': 'In Progress',
            'project': {'key': 'TEST', 'name': 'Test Project', 'id': '10000'},
            'summary': 'Test issue summary',
            'created': '2024-01-01T10:00:00+00:00',
            'updated': '2024-01-15T15:30:00+00:00',
            'status_change_date': '2024-01-10T14:00:00+00:00',
            'reporter': {'display_name': 'John Doe'},
            'assignee': {'display_name': 'Jane Smith'},
            'labels': ['label1', 'label2'],
            'components': [{'name': 'Frontend'}, {'name': 'Backend'}]
        },
        'issue_description': 'This is a test issue description.',
        'issue_comments': [
            {'created_at': '2024-01-02T10:00:00+00:00', 'body': 'First comment', 'author': 'John Doe'},
            {'created_at': '2024-01-03T11:00:00+00:00', 'body': 'Second comment', 'author': 'Jane Smith'}
        ],
        'metrics': {
            'working_minutes_from_create': 7200,
            'working_minutes_in_current_status': 2880,
            'working_minutes_from_first_move': 4320,
            'backlog_minutes': 1440,
            'processing_minutes': 5760,
            'waiting_minutes': 0,
            'total_transitions': 3,
            'backflow_count': 1,
            'unique_statuses_visited': ['Open', 'In Progress', 'In Review'],
            'todo_exit_date': '2024-01-03T09:00:00+00:00'
        },
        'status_transitions': [
            {
                'from_status': 'Open',
                'to_status': 'In Progress',
                'transition_date': '2024-01-10T14:00:00+00:00',
                'minutes_in_previous_status': 1440,
                'is_forward_transition': True,
                'is_backflow': False,
                'author': 'John Doe'
            }
        ],
        'field_changes': [
            {
                'change_date': '2024-01-04T14:30:00+00:00',
                'author': 'Jane Smith',
                'changes': [
                    {
                        'field': 'assignee',
                        'fieldtype': 'jira',
                        'from': 'John Doe',
                        'to': 'Jane Smith'
                    }
                ]
            }
        ]
    }
    
    try:
        # Test the formatter
        doc, doc_id = ElasticsearchDocumentFormatter.format_issue_record(sample_record)
        
        print(f"✅ Document ID: {doc_id}")
        print(f"✅ Document keys: {list(doc.keys())}")
        
        # Check key fields
        assert doc_id == '12345', f"Expected doc_id '12345', got '{doc_id}'"
        assert doc['@timestamp'] == '2024-01-15T15:30:00+00:00', "Timestamp not set correctly"
        assert doc['issue']['key'] == 'TEST-123', "Issue key not set correctly"
        assert doc['issue']['working_minutes'] == 7200, "working_minutes_from_create not mapped correctly"
        assert doc['issue']['status']['working_minutes'] == 2880, "working_minutes_in_current_status not mapped correctly"
        assert doc['backlog']['working_minutes'] == 1440, "backlog_minutes not mapped correctly"
        assert doc['processing']['working_minutes'] == 5760, "processing_minutes not mapped correctly"
        assert doc['total_transitions'] == 3, "total_transitions not mapped correctly"
        assert doc['backflow_count'] == 1, "backflow_count not mapped correctly"
        assert len(doc['status_transitions']) == 1, "status_transitions not mapped correctly"
        assert len(doc['field_changes']) == 1, "field_changes not mapped correctly"
        assert 'First comment Second comment' in doc['comment'], "Comments not concatenated correctly"
        
        print("✅ All assertions passed!")
        
        print("✅ Issue record formatting works correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing issue formatting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test that issue record formatting handles edge cases."""
    print("\nTesting edge cases for issue records...")
    
    # Test with minimal issue record
    minimal_record = {
        'issue_data': {
            'id': '123',
            'key': 'TEST-123',
            'type': 'Bug',
            'status': 'Open',
            'project': {'key': 'TEST', 'name': 'Test Project', 'id': '10000'},
            'summary': 'Minimal test issue',
            'created': '2024-01-01T10:00:00+00:00',
            'updated': '2024-01-01T10:00:00+00:00'
        },
        'metrics': {},
        'status_transitions': [],
        'field_changes': []
    }
    
    try:
        # Test that minimal issue records work
        doc, doc_id = ElasticsearchDocumentFormatter.format_issue_record(minimal_record)
        assert doc_id == '123', f"Expected doc_id '123', got '{doc_id}'"
        assert doc['issue']['key'] == 'TEST-123', "Issue key not set correctly"
        
        print("✅ Minimal issue record formatting works!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing edge cases: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing ES Issue Record Formatting")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Suppress debug logs for cleaner output
    
    success = True
    success &= test_issue_formatting()
    success &= test_edge_cases()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! ES issue formatting is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)
