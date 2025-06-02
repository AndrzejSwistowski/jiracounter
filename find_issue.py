#!/usr/bin/env python3
"""
Find a valid issue key for testing.
"""

from jiraservice import JiraService

def find_valid_issue():
    try:
        js = JiraService()
        issues = js.search_issues('updated >= "-30d"', max_issues=1)
        if issues:
            print(f"Available issue: {issues[0]['key']}")
            return issues[0]['key']
        else:
            print("No issues found")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    find_valid_issue()
