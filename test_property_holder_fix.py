"""
Test script for verifying the PropertyHolder fix
"""
import logging
import sys
from issue_data_extractor import IssueDataExtractor
from jira_field_manager import JiraFieldManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PropertyHolderTest")

class PropertyHolderMock:
    """Mock class that simulates a PropertyHolder object in JIRA"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return "PropertyHolderMock"

def create_mock_jira_issue():
    """Create a mock JIRA issue with a PropertyHolder-like structure"""
    fields = PropertyHolderMock(
        summary="Test issue",
        description="Test description",
        issuetype=PropertyHolderMock(name="Bug"),
        status=PropertyHolderMock(name="Open"),
        priority=PropertyHolderMock(name="High"),
        resolution=None,
        created="2025-05-28T09:00:00.000+0200",
        updated="2025-05-28T09:30:00.000+0200",
        resolutiondate=None,
        assignee=PropertyHolderMock(
            displayName="Test User",
            key="test.user",
            name="test.user",
            emailAddress="test.user@example.com"
        ),
        reporter=PropertyHolderMock(
            displayName="Admin User",
            key="admin.user",
            name="admin.user",
            emailAddress="admin.user@example.com"
        ),
        project=PropertyHolderMock(
            key="TEST",
            name="Test Project",
            id="10000"
        ),
        components=[
            PropertyHolderMock(
                id="20000",
                name="Component 1",
                description="First component"
            )
        ],
        labels=["label1", "label2"],
        parent=PropertyHolderMock(
            id="30000",
            key="TEST-1",
            fields=PropertyHolderMock(
                summary="Parent issue"
            )
        ),
        timetracking=PropertyHolderMock(
            originalEstimate="1d",
            remainingEstimate="4h",
            timeSpent="4h",
            originalEstimateSeconds=28800,
            remainingEstimateSeconds=14400,
            timeSpentSeconds=14400
        )
    )
    
    issue = PropertyHolderMock(
        id="40000",
        key="TEST-2",
        fields=fields
    )
    
    return issue

def test_property_holder_fix():
    """Test that our PropertyHolder fix works correctly"""
    try:
        # Create a mock field manager
        field_manager = JiraFieldManager()
        field_manager.field_ids = {
            'rodzaj_pracy': 'customfield_10001',
            'data_zmiany_statusu': 'customfield_10002',
            'Epic Link': 'customfield_10003',
            'Epic Name': 'customfield_10004',
            'Story Points': 'customfield_10005'
        }
        
        # Create a mock issue with PropertyHolder objects
        test_issue = create_mock_jira_issue()
        
        # Create an instance of the IssueDataExtractor
        extractor = IssueDataExtractor(field_manager)
        
        # Call extract_issue_data with our mock issue
        issue_data = extractor.extract_issue_data(test_issue)
        
        # Print out key fields to verify they were extracted correctly
        print("\n--- TEST RESULTS ---")
        print(f"Key: {issue_data['key']}")
        print(f"Summary: {issue_data['summary']}")
        print(f"Issue Type: {issue_data['issue_type']}")
        print(f"Status: {issue_data['status']}")
        print(f"Priority: {issue_data['priority']}")
        
        # Check that parent issue was extracted correctly
        if issue_data['parent_issue']:
            print(f"Parent Key: {issue_data['parent_issue']['key']}")
            print(f"Parent Summary: {issue_data['parent_issue']['summary']}")
        else:
            print("WARNING: Parent issue is None")
            
        print("--- TEST PASSED ---")
        return True
    except Exception as e:
        import traceback
        print(f"\n--- TEST FAILED ---")
        print(f"Error: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Testing PropertyHolder fix...")
    success = test_property_holder_fix()
    sys.exit(0 if success else 1)
