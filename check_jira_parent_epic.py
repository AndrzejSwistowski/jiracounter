"""
Test script to verify that JiraService correctly retrieves parent, epic, labels, and components for a specific issue.
And checks if parent issue has an epic linked to it that can be inherited.

This script will:
1. Connect to Jira
2. Fetch a specific issue (BAI-596)
3. Extract and display parent issue, epic, labels, and components
4. If no epic is found, check if the parent issue has an epic linked
5. Verify the correct extraction of these fields before repopulating Elasticsearch
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
    Also checks if parent issue has an epic that can be inherited.
    
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
            
            # Get the full parent issue data to check for epic link
            parent_full_issue = jira_service.get_issue(parent_issue.get('key'))
            if parent_full_issue:
                print("\n=== Parent Issue Details ===")
                parent_epic = parent_full_issue.get('epic_issue')
                if parent_epic:
                    print(f"Parent Epic Key: {parent_epic.get('key')}")
                    print(f"Parent Epic ID: {parent_epic.get('id')}")
                    print(f"Parent Epic Summary: {parent_epic.get('summary')}")
                    print("\n*** This could be inherited by the child issue! ***")
                else:
                    print("Parent issue has no epic linked")
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
            print("No epic found directly linked to this issue")
        
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
        
        # Suggestion for improvement to JiraService
        if not epic_issue and parent_issue and parent_full_issue and parent_full_issue.get('epic_issue'):
            print("\n=== Suggested Improvement ===")
            print("Currently, the JiraService doesn't inherit the epic from parent issues.")
            print("It would be beneficial to update the JiraService to check for epics in parent issues when no epic is directly linked.")
            parent_epic = parent_full_issue.get('epic_issue')
            print(f"This issue could inherit epic {parent_epic.get('key')} - {parent_epic.get('summary')}")
        
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