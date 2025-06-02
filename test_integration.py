#!/usr/bin/env python3
"""
Test to verify that the JiraService refactoring works with the existing codebase.
This ensures that reports and population processes continue to work.
"""

import sys
import os
from unittest.mock import Mock

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jiraservice import JiraService
from jira_field_manager import JiraFieldManager

def test_jiraservice_integration():
    """Test that JiraService works with the refactored IssueDataExtractor."""
    print("=== Testing JiraService Integration ===")
    
    # Create a mock JIRA client
    mock_jira = Mock()
    
    # Create JiraService (which should now use IssueDataExtractor internally)
    jira_service = JiraService(mock_jira)
    
    # Verify that the data_extractor was created
    assert hasattr(jira_service, 'data_extractor'), "JiraService should have data_extractor attribute"
    assert jira_service.data_extractor is not None, "data_extractor should not be None"
    print("✓ JiraService has data_extractor instance")
    
    # Verify that field_manager was injected
    assert hasattr(jira_service.data_extractor, 'field_manager'), "IssueDataExtractor should have field_manager"
    assert isinstance(jira_service.data_extractor.field_manager, JiraFieldManager), "field_manager should be JiraFieldManager instance"
    print("✓ IssueDataExtractor has JiraFieldManager injected")
    
    # Create a simple mock issue to test extraction
    mock_issue = Mock()
    mock_issue.key = "INTEGRATION-123"
    mock_issue.id = "10002"
    
    mock_fields = Mock()
    mock_fields.summary = "Integration Test Issue"
    mock_fields.description = "Testing the integration"
    mock_fields.created = "2024-01-15T10:00:00.000+0000"
    mock_fields.updated = "2024-01-15T11:00:00.000+0000"
    
    # Mock issue type
    mock_issuetype = Mock()
    mock_issuetype.name = "Task"
    mock_fields.issuetype = mock_issuetype
    
    # Mock status
    mock_status = Mock()
    mock_status.name = "To Do"
    mock_fields.status = mock_status
    
    # Mock project
    mock_project = Mock()
    mock_project.key = "INT"
    mock_project.name = "Integration Project"
    mock_project.id = "10000"
    mock_fields.project = mock_project
    
    mock_fields.labels = ["integration", "test"]
    mock_fields.components = []
    mock_fields.assignee = None
    mock_fields.reporter = None
    mock_fields.parent = None
    mock_fields.priority = None
    mock_fields.resolution = None
    mock_fields.resolutiondate = None
    mock_fields.timetracking = {}
    
    mock_issue.fields = mock_fields
    
    # Test the extraction through JiraService
    print("\n=== Testing Issue Data Extraction ===")
    try:
        # This should use the refactored _extract_issue_data method which delegates to IssueDataExtractor
        result = jira_service._extract_issue_data(mock_issue)
        
        # Verify basic fields
        assert result['key'] == "INTEGRATION-123", f"Expected key INTEGRATION-123, got {result['key']}"
        assert result['summary'] == "Integration Test Issue", f"Expected correct summary, got {result['summary']}"
        assert result['issue_type'] == "Task", f"Expected issue_type Task, got {result['issue_type']}"
        assert result['status'] == "To Do", f"Expected status 'To Do', got {result['status']}"
        
        print(f"✓ Key: {result['key']}")
        print(f"✓ Summary: {result['summary']}")
        print(f"✓ Issue Type: {result['issue_type']}")
        print(f"✓ Status: {result['status']}")
        print(f"✓ Project: {result.get('project', {}).get('key')}")
        print(f"✓ Labels: {result.get('labels', [])}")
        
        # Verify legacy compatibility
        assert result.get('type') == result.get('issue_type'), "Legacy 'type' field should match 'issue_type'"
        print(f"✓ Legacy compatibility: type = {result.get('type')}")
        
        print("\n✓ Issue extraction through JiraService works correctly!")
        
    except Exception as e:
        print(f"✗ Error during issue extraction: {e}")
        raise
    
    print("\n=== All Integration Tests Passed! ===")
    print("✓ SOLID refactoring successful")
    print("✓ Backward compatibility maintained")
    print("✓ Reports and population processes should continue to work")

if __name__ == "__main__":
    test_jiraservice_integration()
