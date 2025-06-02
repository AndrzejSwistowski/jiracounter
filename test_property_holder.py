"""
Test script to verify that PropertyHolder objects are handled correctly.
"""

import logging
import sys
import os
from jira_field_manager import JiraFieldManager
from issue_data_extractor import IssueDataExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create mock PropertyHolder class for testing
class MockPropertyHolder:
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return f"MockPropertyHolder({self.name})"

# Create a mock PropertyHolder-like object that lacks the get() method
class MockParent:
    def __init__(self):
        self.id = "PARENT-123"
        self.key = "PARENT-KEY"
        self.fields = MockFields()

class MockFields:
    def __init__(self):
        self.summary = "Parent Summary"
        self.description = "Parent Description"
        self.issuetype = MockIssueType()
        self.status = MockStatus()
        self.priority = MockPriority()
        self.resolution = None
        self.created = "2023-05-27T10:00:00.000+0000"
        self.updated = "2023-05-28T10:00:00.000+0000"
        self.resolutiondate = None
        self.assignee = MockUser("john")
        self.reporter = MockUser("jane")
        self.project = MockProject()
        self.components = [MockComponent("Component1"), MockComponent("Component2")]
        self.labels = ["label1", "label2"]
        self.parent = MockParent()
        self.timetracking = MockTimeTracking()

class MockIssueType:
    def __init__(self):
        self.name = "Task"
        self.id = "10001"

class MockStatus:
    def __init__(self):
        self.name = "In Progress"
        self.id = "3"

class MockPriority:
    def __init__(self):
        self.name = "Medium"
        self.id = "2"

class MockUser:
    def __init__(self, key):
        self.displayName = f"{key.title()} Doe"
        self.key = key
        self.name = key
        self.emailAddress = f"{key}@example.com"

class MockProject:
    def __init__(self):
        self.key = "TEST"
        self.name = "Test Project"
        self.id = "10000"

class MockComponent:
    def __init__(self, name):
        self.id = f"comp-{name.lower()}"
        self.name = name
        self.description = f"Description of {name}"

class MockTimeTracking:
    def __init__(self):
        self.originalEstimate = "1d"
        self.remainingEstimate = "4h"
        self.timeSpent = "4h"
        self.originalEstimateSeconds = 28800
        self.remainingEstimateSeconds = 14400
        self.timeSpentSeconds = 14400

# Create a mock issue
class MockIssue:
    def __init__(self):
        self.id = "TEST-123"
        self.key = "TEST-123"
        self.fields = MockFields()

def main():
    """Run tests for PropertyHolder object handling"""
    try:
        # Create field manager and extractor
        field_manager = JiraFieldManager()
        extractor = IssueDataExtractor(field_manager)
        
        # Create a mock issue
        issue = MockIssue()
        
        # Extract issue data
        logger.info("Extracting issue data...")
        issue_data = extractor.extract_issue_data(issue)
        
        # Log the extracted data
        logger.info("Successfully extracted data from issue")
        logger.info(f"Issue key: {issue_data.get('key')}")
        logger.info(f"Issue summary: {issue_data.get('summary')}")
        logger.info(f"Issue type: {issue_data.get('issue_type')}")
        logger.info(f"Issue status: {issue_data.get('status')}")
        
        # Test parent issue handling
        logger.info("Parent issue data:")
        if issue_data.get('parent_issue'):
            logger.info(f"  Parent key: {issue_data['parent_issue'].get('key')}")
            logger.info(f"  Parent summary: {issue_data['parent_issue'].get('summary')}")
        else:
            logger.info("No parent issue found")
        
        # Test components
        logger.info("Components:")
        for comp in issue_data.get('components', []):
            logger.info(f"  {comp.get('name')}")
        
        logger.info("Test completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
