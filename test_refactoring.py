#!/usr/bin/env python3
"""
Test script to validate the SOLID refactoring of JiraService.
"""

from jiraservice import JiraService
import json

def test_extraction():
    """Test the refactored _extract_issue_data method."""
    # Create a mock JIRA issue for testing
    mock_issue = {
        'key': 'TEST-123',
        'id': '12345',
        'fields': {
            'summary': 'Test Issue Summary',
            'description': 'Test issue description',
            'issuetype': {'name': 'Story'},
            'status': {'name': 'In Progress'},
            'priority': {'name': 'High'},
            'created': '2024-01-01T10:00:00.000+0000',
            'updated': '2024-01-02T15:30:00.000+0000',
            'assignee': {
                'key': 'testuser',
                'name': 'testuser',
                'displayName': 'Test User',
                'emailAddress': 'test@example.com'
            },
            'project': {
                'key': 'TEST',
                'name': 'Test Project',
                'id': '10000'
            },
            'labels': ['label1', 'label2'],
            'components': [
                {'id': '1', 'name': 'Component1', 'description': 'Test component'}
            ]
        }
    }

    # Test the extraction
    service = JiraService()
    result = service._extract_issue_data(mock_issue)

    print('Extraction test results:')
    print(f'Issue key: {result.get("key")}')
    print(f'Issue summary: {result.get("summary")}')
    print(f'Issue type: {result.get("issue_type")}')
    print(f'Status: {result.get("status")}')
    print(f'Created: {result.get("created")}')
    print(f'Assignee: {result.get("assignee", {}).get("display_name")}')
    print(f'Project: {result.get("project", {}).get("name")}')
    print(f'Labels: {result.get("labels")}')
    print(f'Components: {[c.get("name") for c in result.get("components", [])]}')

    print('\nExtraction completed successfully!')
    
    # Validate some key fields
    assert result.get('key') == 'TEST-123'
    assert result.get('summary') == 'Test Issue Summary'
    assert result.get('issue_type') == 'Story'
    assert result.get('status') == 'In Progress'
    assert result.get('assignee', {}).get('display_name') == 'Test User'
    assert result.get('project', {}).get('name') == 'Test Project'
    assert result.get('labels') == ['label1', 'label2']
    
    print('All assertions passed!')

if __name__ == '__main__':
    test_extraction()
