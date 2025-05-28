"""
Test script for PropertyHolder fix
"""
import logging
from issue_data_extractor import IssueDataExtractor
from jira_field_manager import JiraFieldManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

class PropertyHolderMock:
    """Mock for PropertyHolder objects that don't have 'get' method"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return "PropertyHolder Mock Object"

def test_property_holder_parent():
    """Test parent issue extraction with PropertyHolder objects"""
    # Create a mock field manager
    field_manager = JiraFieldManager()
    
    # Create a PropertyHolder-like object for parent
    parent = PropertyHolderMock(
        id="12345",
        key="TEST-1",
        fields=PropertyHolderMock(
            summary="Parent Issue"
        )
    )
    
    # Create a PropertyHolder-like object for the issue
    issue = PropertyHolderMock(
        id="67890",
        key="TEST-2",
        fields=PropertyHolderMock(
            summary="Test Issue",
            parent=parent
        )
    )
    
    # Create the extractor
    extractor = IssueDataExtractor(field_manager)
    
    # Test the extraction
    try:
        result = extractor.extract_issue_data(issue)
        
        # Print the parent issue data
        print("Parent issue data:")
        print(f"  ID: {result.get('parent_issue', {}).get('id')}")
        print(f"  Key: {result.get('parent_issue', {}).get('key')}")
        print(f"  Summary: {result.get('parent_issue', {}).get('summary')}")
        
        if result.get('parent_issue'):
            print("✅ Successfully extracted parent issue data!")
        else:
            print("❌ Failed to extract parent issue data")
    except Exception as e:
        print(f"❌ Error during extraction: {e}")

if __name__ == "__main__":
    test_property_holder_parent()
