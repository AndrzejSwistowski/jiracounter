"""
Test script for the JiraService class.

This script tests basic functionality of the JiraService,
including connection, project listing, and issue searching.
"""
import sys
import os
import codecs
from jiraservice import JiraService
import config

# Force UTF-8 output encoding
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def test_connection():
    """Test basic connection to Jira."""
    print("Testing connection to Jira...")
    
    try:
        service = get_connection()
        print(f"[SUCCESS] Successfully connected to {config.JIRA_BASE_URL}")
        return service
    except Exception as e:
        print(f"[ERROR] Connection failed: {str(e)}")
        sys.exit(1)

def get_connection():
    service = JiraService()    
    try:
        service.connect()
        return service
    except Exception as e:
        sys.exit(1)

def test_projects(service = None):
    """List available projects."""
    if service is None:
        service = get_connection()
        
    print("\nTesting project listing...")
    jira = service.jira_client
    
    try:
        projects = jira.projects()
        print(f"[SUCCESS] Found {len(projects)} projects")
        
        if projects:
            print("\nSample projects:")
            for project in projects[:5]:  # Show first 5 projects
                print(f"- {project.name} ({project.key})")
        else:
            print("No projects found. Check your permissions.")
    except Exception as e:
        print(f"[ERROR] Project listing failed: {str(e)}")

def test_search_issues(service = None):
    """Test searching for issues."""
    if service is None:
        service = get_connection()
        
    print("\nTesting issue search...")
    
    # Example JQL: issues updated in the last 7 days
    jql = "updated >= -7d ORDER BY updated DESC"
    
    try:
        issues = service.search_issues(jql)
        print(f"[SUCCESS] Search successful, found {len(issues)} recent issues")
        
        if issues:
            print("\nSample issues:")
            for issue in issues[:30]:  # Show first 5 issues
                print(f"- {issue['key']}: {issue['summary']} ({issue['status']})")
                # Display components for each issue in search results
                if 'components' in issue and issue['components']:
                    component_names = [comp['name'] for comp in issue['components']]
                    print(f"  Components: {', '.join(component_names)}")
                # Display labels for each issue in search results
                if 'labels' in issue and issue['labels']:
                    print(f"  Labels: {', '.join(issue['labels'])}")
            return issues  # Return the issues found
        else:
            print("No matching issues found.")
            return []  # Return an empty list if no issues found
    except Exception as e:
        print(f"[ERROR] Issue search failed: {str(e)}")
        return []  # Return an empty list on error

def test_get_issue(service=None):
    """Test retrieving a specific issue."""
    if service is None:
        service = get_connection()
        
    print("\nTesting issue retrieval...")
    
    # Try to get an issue from previous search results if available
    try:
        # Search for any issue to use as a test
        issues = service.search_issues("key = BZPB-25")
        if not issues:
            print("[ERROR] No issues found to test issue retrieval")
            return
            
        test_issue_key = issues[0]["key"]
        print(f"Using issue {test_issue_key} for testing...")
        
        issue_details = service.get_issue(test_issue_key)
        print(f"[SUCCESS] Successfully retrieved issue: {test_issue_key}")
        print(f"  Summary: {issue_details['summary']}")
        print(f"  Status: {issue_details['status']}")
        print(f"  Assignee: {issue_details['assignee']}")
        print(f"  Created: {issue_details['created']}")
        print(f"  Updated: {issue_details['updated']}")
        
        # Display component information
        if 'components' in issue_details and issue_details['components']:
            print(f"  Components ({len(issue_details['components'])}):")
            for component in issue_details['components']:
                comp_info = f"    - {component['name']} (ID: {component['id']})"
                if 'description' in component and component['description']:
                    comp_info += f" - {component['description']}"
                print(comp_info)
        else:
            print("  Components: None")
            
        # Display labels information
        if 'labels' in issue_details and issue_details['labels']:
            print(f"  Labels: {', '.join(issue_details['labels'])}")
        else:
            print("  Labels: None")
    except Exception as e:
        print(f"[ERROR] Issue retrieval failed: {str(e)}")




def test_get_issue_changelog(service=None):
    """Test retrieving changelog for a specific issue."""
    if service is None:
        service = get_connection()
        
    print("\nTesting issue changelog retrieval...")
    
    try:
        # Search for any issue to use as a test
        issues = service.search_issues("key='BZPB-174'")
        if not issues:
            print("[ERROR] No issues found to test changelog retrieval")
            return
            
        test_issue_key = issues[0]["key"]
        print(f"Using issue {test_issue_key} for changelog testing...")
        
        changelog_data = service.get_issue_changelog(test_issue_key)
        print(f"[SUCCESS] Successfully retrieved changelog for issue: {test_issue_key}")
        
        if changelog_data:
            # Display basic issue information
            issue_data = changelog_data.get('issue_data', {})
            print(f"  Issue: {issue_data.get('issueKey', 'Unknown')} - {issue_data.get('summary', 'No summary')}")
            print(f"  Status: {issue_data.get('status', 'Unknown')}")
            
            # Display metrics summary
            metrics = changelog_data.get('metrics', {})
            print(f"  Transitions: {metrics.get('total_transitions', 0)}")
            print(f"  Working minutes from creation: {metrics.get('working_minutes_from_create', 0)}")
            
            # Display status transitions
            status_transitions = changelog_data.get('status_transitions', [])
            if status_transitions:
                print(f"  Found {len(status_transitions)} status transitions:")
                for transition in status_transitions[:3]:  # Show first 3 transitions
                    print(f"    - {transition.get('from_status', 'Unknown')} → {transition.get('to_status', 'Unknown')} "
                          f"by {transition.get('author', 'Unknown')} on {transition.get('transition_date', 'Unknown')}")
            
            # Display field changes
            field_changes = changelog_data.get('field_changes', [])
            if field_changes:
                print(f"  Found {len(field_changes)} field change events:")
                for change_event in field_changes[:3]:  # Show first 3 change events
                    print(f"    - Changed by {change_event.get('author', 'Unknown')} on {change_event.get('change_date', 'Unknown')}")
                    for change in change_event.get('changes', [])[:2]:  # Show first 2 changes per event
                        print(f"      - {change.get('field', 'Unknown')}: {change.get('from', 'N/A')} → {change.get('to', 'N/A')}")
                    
        else:
            print("  No changelog data found for this issue")
    except Exception as e:
        print(f"[ERROR] Changelog retrieval failed: {str(e)}")

def check_api_token():
    """Check if API token is set."""
    if not config.JIRA_API_TOKEN:
        print("\n[WARNING] JIRA_API_TOKEN is not set")
        print("To set it in the environment, run:")
        if os.name == 'nt':  # Windows
            print("set JIRA_API_TOKEN=your_token_here")
        else:  # Unix/Linux/Mac
            print("export JIRA_API_TOKEN=your_token_here")
        print("\nOr edit config.py to include the token directly")
        return False
    return True

# Runner functions for direct execution from the IDE
def run_test_projects():
    """Run only the test_projects function - call this directly from the IDE."""
    if not check_api_token():
        sys.exit(1)
    service = test_connection()
    test_projects(service)

def run_test_search_issues():
    """Run only the test_search_issues function - call this directly from the IDE."""
    if not check_api_token():
        sys.exit(1)
    service = test_connection()
    test_search_issues(service)

def run_test_get_issue():
    """Run only the test_get_issue function - call this directly from the IDE."""
    if not check_api_token():
        sys.exit(1)
    service = test_connection()
    test_get_issue(service)

def run_test_get_issue_changelog():
    """Run only the test_get_issue_changelog function - call this directly from the IDE."""
    if not check_api_token():
        sys.exit(1)
    service = test_connection()
    test_get_issue_changelog(service)

if __name__ == "__main__":
    print("Jira Service Test Script")
    print("=" * 30)
    print(f"Base URL: {config.JIRA_BASE_URL}")
    print(f"Username: {config.JIRA_USERNAME}")
    print("-" * 30)
    
    if not check_api_token():
        sys.exit(1)
    
    # Check for specific test execution parameters
    import argparse
    parser = argparse.ArgumentParser(description='Run Jira service tests')
    parser.add_argument('--test', type=str, help='Specific test to run (projects, search, issue, changelog)')
    args = parser.parse_args()
    
    # Always establish connection first
    service = test_connection()
    
    if args.test == 'projects':
        # Run only the projects test
        test_projects(service)
    elif args.test == 'search':
        # Run only the search issues test
        test_search_issues(service)
    elif args.test == 'issue':
        # Run only the get issue test
        test_get_issue(service)
    elif args.test == 'changelog':
        # Run only the changelog test
        test_get_issue_changelog(service)
    else:
        # Run all tests
        test_projects(service)
        test_search_issues(service)
        test_get_issue(service)
        test_get_issue_changelog(service)
    
    print("\nAll tests completed.")