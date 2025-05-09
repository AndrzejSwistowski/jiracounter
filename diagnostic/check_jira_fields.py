"""
Test script to verify that JiraService correctly retrieves parent, epic, labels, and components for a specific issue.

This script will:
1. Connect to Jira
2. Fetch a specific issue (BAI-596)
3. Extract and display parent issue, epic, labels, and components
4. Verify the correct extraction of these fields before repopulating Elasticsearch
"""

import logging
import sys
from jiraservice import JiraService
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_issue_fields(issue_key):
    """
    Check if the parent, epic, labels, and components for a specific issue are correctly retrieved.
    
    Args:
        issue_key: The Jira issue key to check (e.g., BAI-596)
    """
    try:
        # Initialize Jira Service
        jira_service = JiraService()
        
        # Fetch the issue using JiraService methods
        issue = jira_service.get_issue(issue_key)
        
        if not issue:
            logger.error(f"Issue {issue_key} not found")
            return False
        
        logger.info(f"Successfully retrieved issue: {issue_key} - {issue.get('summary', 'No summary')}")
        
        # Get issue fields from JiraService
        print("\n=== Issue Details ===")
        print(f"Issue Key: {issue_key}")
        print(f"Summary: {issue.get('summary', 'No summary')}")
        
        # Extract parent issue
        parent_issue = issue.get('parent_issue')
        print("\n=== Parent Issue ===")
        if parent_issue:
            print(f"Parent Key: {parent_issue.get('key')}")
            print(f"Parent ID: {parent_issue.get('id')}")
            print(f"Parent Summary: {parent_issue.get('summary')}")
        else:
            print("No parent issue found")
        
        # Extract epic
        epic_issue = issue.get('epic_issue')
        print("\n=== Epic ===")
        if epic_issue:
            print(f"Epic Key: {epic_issue.get('key')}")
            print(f"Epic ID: {epic_issue.get('id')}")
            print(f"Epic Summary: {epic_issue.get('summary')}")
        else:
            print("No epic found")
        
        # Extract labels
        print("\n=== Labels ===")
        labels = issue.get('labels', [])
        if labels:
            for label in labels:
                print(f"- {label}")
        else:
            print("No labels found")
        
        # Extract components
        print("\n=== Components ===")
        components = issue.get('components', [])
        if components:
            for component in components:
                print(f"- {component.get('name')} (ID: {component.get('id')})")
        else:
            print("No components found")
        
        return True
    except Exception as e:
        logger.error(f"Error checking issue fields: {e}")
        return False

if __name__ == "__main__":
    issue_key = "BAI-596"
    if len(sys.argv) > 1:
        issue_key = sys.argv[1]
    
    success = check_issue_fields(issue_key)
    sys.exit(0 if success else 1)