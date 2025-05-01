"""
Test script for the JiraService class.

This script tests basic functionality of the JiraService,
including connection, project listing, and issue searching.
"""
import sys
import os
from jiraservice import JiraService
import config

def test_connection():
    """Test basic connection to Jira."""
    print("Testing connection to Jira...")
    service = JiraService()
    
    try:
        jira = service.connect()
        print(f"✅ Successfully connected to {config.JIRA_BASE_URL}")
        return service
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        sys.exit(1)

def test_projects(service):
    """List available projects."""
    print("\nTesting project listing...")
    jira = service.jira_client
    
    try:
        projects = jira.projects()
        print(f"✅ Found {len(projects)} projects")
        
        if projects:
            print("\nSample projects:")
            for project in projects[:5]:  # Show first 5 projects
                print(f"- {project.name} ({project.key})")
        else:
            print("No projects found. Check your permissions.")
    except Exception as e:
        print(f"❌ Project listing failed: {str(e)}")

def test_search_issues(service):
    """Test searching for issues."""
    print("\nTesting issue search...")
    
    # Example JQL: issues updated in the last 7 days
    jql = "updated >= -7d ORDER BY updated DESC"
    
    try:
        issues = service.search_issues(jql)
        print(f"✅ Search successful, found {len(issues)} recent issues")
        
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
        print(f"❌ Issue search failed: {str(e)}")
        return []  # Return an empty list on error

def test_get_issue(service):
    """Test retrieving a specific issue."""
    print("\nTesting issue retrieval...")
    
    # Try to get an issue from previous search results if available
    try:
        # Search for any issue to use as a test
        issues = service.search_issues("updated >= -3d")
        if not issues:
            print("❌ No issues found to test issue retrieval")
            return
            
        test_issue_key = issues[0]["key"]
        print(f"Using issue {test_issue_key} for testing...")
        
        issue_details = service.get_issue(test_issue_key)
        print(f"✅ Successfully retrieved issue: {test_issue_key}")
        print(f"  Summary: {issue_details['summary']}")
        print(f"  Status: {issue_details['status']}")
        print(f"  Assignee: {issue_details['assignee']}")
        print(f"  Created: {issue_details['created']}")
        print(f"  Updated: {issue_details['updated']}")
        
        # Display component information
        if 'components' in issue_details and issue_details['components']:
            print(f"  Components ({len(issue_details['components'])}):")
            for component in issue_details['components']:
                comp_info = f"    • {component['name']} (ID: {component['id']})"
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
        print(f"❌ Issue retrieval failed: {str(e)}")

def test_get_issue_changelog(service):
    """Test retrieving changelog for a specific issue."""
    print("\nTesting issue changelog retrieval...")
    
    try:
        # Search for any issue to use as a test
        issues = service.search_issues("key='BZPB-343'")
        if not issues:
            print("❌ No issues found to test changelog retrieval")
            return
            
        test_issue_key = issues[0]["key"]
        print(f"Using issue {test_issue_key} for changelog testing...")
        
        changelog = service.get_issue_changelog(test_issue_key)
        print(f"✅ Successfully retrieved changelog for issue: {test_issue_key}")
        
        if changelog:
            print(f"  Found {len(changelog)} changelog entries")
            
            # Display a few recent changelog entries
            for entry in changelog:  # Show first 3 entries
                print(f"  - History ID: {entry['id']} | Changed by {entry['author']} on {entry['created_date']}")
                
                # Show the changes in this entry
                for change in entry['changes']:  # Show first 2 changes per entry
                    print(f"    • {change['field']}: {change['from']} → {change['to']}")
                    
        else:
            print("  No changelog entries found for this issue")
    except Exception as e:
        print(f"❌ Changelog retrieval failed: {str(e)}")

def check_api_token():
    """Check if API token is set."""
    if not config.JIRA_API_TOKEN:
        print("\n⚠️  WARNING: JIRA_API_TOKEN is not set")
        print("To set it in the environment, run:")
        if os.name == 'nt':  # Windows
            print("set JIRA_API_TOKEN=your_token_here")
        else:  # Unix/Linux/Mac
            print("export JIRA_API_TOKEN=your_token_here")
        print("\nOr edit config.py to include the token directly")
        return False
    return True

if __name__ == "__main__":
    print("Jira Service Test Script")
    print("=" * 30)
    print(f"Base URL: {config.JIRA_BASE_URL}")
    print(f"Username: {config.JIRA_USERNAME}")
    print("-" * 30)
    
    if not check_api_token():
        sys.exit(1)
    
    # Run tests
    service = test_connection()
    test_projects(service)
    test_search_issues(service)
    test_get_issue(service)
    test_get_issue_changelog(service)
    
    print("\nAll tests completed.")