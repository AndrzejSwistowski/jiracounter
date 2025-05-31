#!/usr/bin/env python3
"""
End-to-end test for the comprehensive record flow:
1. Extract comprehensive record from issue history extractor
2. Format for ES using document formatter  
3. Populate ES using the populator

This test uses mock data to avoid dependency on live JIRA.
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from issue_history_extractor import IssueHistoryExtractor
from es_document_formatter import ElasticsearchDocumentFormatter
from es_populate import JiraElasticsearchPopulator

class MockIssue:
    """Mock JIRA issue for testing."""
    def __init__(self):
        self.id = "12345"
        self.key = "TEST-123"
        
        # Mock fields
        self.fields = MockFields()
        
        # Mock changelog
        self.changelog = MockChangelog()

class MockFields:
    """Mock JIRA issue fields."""
    def __init__(self):
        self.summary = "Test Issue Summary"
        self.description = "This is a test issue description."
        self.created = "2024-01-01T10:00:00+00:00"
        self.updated = "2024-01-15T15:30:00+00:00"
        self.status = MockStatus()
        self.issuetype = MockIssueType()
        self.project = MockProject()
        self.reporter = MockUser("john.doe", "John Doe")
        self.assignee = MockUser("jane.smith", "Jane Smith")
        self.labels = ["label1", "label2"]
        self.components = [MockComponent("Frontend"), MockComponent("Backend")]
        self.comment = MockComments()

class MockStatus:
    def __init__(self):
        self.name = "In Progress"

class MockIssueType:
    def __init__(self):
        self.name = "Story"

class MockProject:
    def __init__(self):
        self.key = "TEST"
        self.name = "Test Project"

class MockUser:
    def __init__(self, name, display_name):
        self.name = name
        self.displayName = display_name

class MockComponent:
    def __init__(self, name):
        self.name = name

class MockComments:
    def __init__(self):
        self.comments = [
            MockComment("2024-01-02T10:00:00+00:00", "First comment", "John Doe"),
            MockComment("2024-01-03T11:00:00+00:00", "Second comment", "Jane Smith")
        ]

class MockComment:
    def __init__(self, created, body, author):
        self.created = created
        self.body = body
        self.author = MockUser("test", author)

class MockChangelog:
    """Mock changelog with status transitions."""
    def __init__(self):
        self.histories = [
            MockHistory("2024-01-10T14:00:00+00:00", [
                MockHistoryItem("status", "Open", "In Progress")
            ])
        ]

class MockHistory:
    def __init__(self, created, items):
        self.created = created
        self.items = items
        self.author = MockUser("john.doe", "John Doe")

class MockHistoryItem:
    def __init__(self, field, from_value, to_value):
        self.field = field
        self.fromString = from_value
        self.toString = to_value

class MockFieldManager:
    """Mock field manager."""
    def get_allocation_code(self, issue):
        return "NEW"

class MockDataExtractor:
    """Mock issue data extractor."""
    def extract_issue_data(self, issue):
        return {
            'issueId': issue.id,
            'key': issue.key,
            'type': issue.fields.issuetype.name,
            'status': issue.fields.status.name,
            'project_key': issue.fields.project.key,
            'summary': issue.fields.summary,
            'created': issue.fields.created,
            'updated': issue.fields.updated,
            'reporter': {'display_name': issue.fields.reporter.displayName},
            'assignee': {'display_name': issue.fields.assignee.displayName},
            'labels': issue.fields.labels,
            'components': [{'name': c.name} for c in issue.fields.components]
        }

def test_comprehensive_flow():
    """Test the complete flow from extraction to ES population."""
    print("Testing comprehensive record flow...")
    
    try:
        # Step 1: Extract comprehensive record
        print("Step 1: Extracting comprehensive record...")
        
        field_manager = MockFieldManager()
        data_extractor = MockDataExtractor()
        extractor = IssueHistoryExtractor(field_manager, data_extractor)
        
        mock_issue = MockIssue()
        comprehensive_record = extractor.extract_issue_changelog(mock_issue, "TEST-123")
        
        print(f"✅ Extracted record with keys: {list(comprehensive_record.keys())}")
        
        # Verify the comprehensive record structure
        assert 'issue_data' in comprehensive_record, "Missing issue_data section"
        assert 'metrics' in comprehensive_record, "Missing metrics section"
        assert 'status_transitions' in comprehensive_record, "Missing status_transitions section"
        assert 'field_changes' in comprehensive_record, "Missing field_changes section"
        assert 'issue_description' in comprehensive_record, "Missing issue_description section"
        assert 'issue_comments' in comprehensive_record, "Missing issue_comments section"
        
        print("✅ Comprehensive record structure is correct")
        
        # Step 2: Format for ES
        print("Step 2: Formatting for Elasticsearch...")
        
        doc, doc_id = ElasticsearchDocumentFormatter.format_comprehensive_record(comprehensive_record)
        
        print(f"✅ Formatted document with ID: {doc_id}")
        print(f"✅ Document has {len(doc)} fields")
        
        # Verify key mappings
        assert doc['@timestamp'] == comprehensive_record['issue_data']['updated'], "Timestamp not mapped correctly"
        assert doc['issue']['key'] == comprehensive_record['issue_data']['key'], "Issue key not mapped correctly"
        assert doc['issue']['working_minutes'] == comprehensive_record['metrics']['working_minutes_from_create'], "working_minutes_from_create not mapped correctly"
        
        print("✅ ES document formatting is correct")
        
        # Step 3: Test ES population logic (without actually connecting to ES)
        print("Step 3: Testing ES population logic...")
        
        populator = JiraElasticsearchPopulator()
        
        # Test record detection
        is_comprehensive = populator._is_comprehensive_record(comprehensive_record)
        assert is_comprehensive, "Should detect as comprehensive record"
        
        # Test document formatting through populator
        formatted_doc, formatted_id = populator.format_comprehensive_record(comprehensive_record)
        assert formatted_doc == doc, "Populator should return same formatted document"
        assert formatted_id == doc_id, "Populator should return same document ID"
        
        print("✅ ES population logic is correct")
        
        # Step 4: Verify the complete data flow integrity
        print("Step 4: Verifying data integrity...")
        
        # Check that metrics from the extractor made it to the ES document
        original_metrics = comprehensive_record['metrics']
        
        assert doc['issue']['working_minutes'] == original_metrics['working_minutes_from_create']
        assert doc['issue']['status']['working_minutes'] == original_metrics['working_minutes_in_current_status']
        assert doc['backlog']['working_minutes'] == original_metrics['backlog_minutes']
        assert doc['processing']['working_minutes'] == original_metrics['processing_minutes']
        assert doc['waiting']['working_minutes'] == original_metrics['waiting_minutes']
        assert doc['total_transitions'] == original_metrics['total_transitions']
        assert doc['backflow_count'] == original_metrics['backflow_count']
        assert doc['unique_statuses_visited'] == original_metrics['unique_statuses_visited']
        
        print("✅ All metrics properly mapped from extraction to ES document")
        
        # Check that transitions and field changes are preserved
        assert len(doc['status_transitions']) == len(comprehensive_record['status_transitions'])
        assert len(doc['field_changes']) == len(comprehensive_record['field_changes'])
        
        print("✅ Status transitions and field changes preserved")
        
        # Check that comments are properly concatenated
        assert 'First comment' in doc['comment']
        assert 'Second comment' in doc['comment']
        
        print("✅ Comments properly concatenated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in comprehensive flow test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Complete Comprehensive Record Flow")
    print("=" * 60)
    
    # Configure logging to reduce noise
    logging.basicConfig(level=logging.WARNING)
    
    success = test_comprehensive_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Complete flow test passed! The restructuring is working correctly.")
        print("\n📊 Summary:")
        print("   ✅ Issue history extraction → comprehensive record")
        print("   ✅ Comprehensive record → ES document formatting")
        print("   ✅ ES document → population logic")
        print("   ✅ Data integrity maintained throughout the flow")
    else:
        print("❌ Flow test failed. Please check the output above.")
        sys.exit(1)
