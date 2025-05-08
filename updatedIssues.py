"""
This module provides functionality to retrieve all issues updated between specified dates from a JIRA server.
The results are grouped by project.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import dateutil.parser
from jiraservice import JiraService
import config
from utils import calculate_days_since_date, validate_and_format_dates

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

class UpdatedIssuesReport:
    """Service class to retrieve information about issues updated between specific dates in Jira projects."""
    
    def __init__(self):
        """Initialize the UpdatedIssuesReport service."""
        self.jira_service = JiraService()
    
    def get_updated_issues(self, start_date: str, end_date: str, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all issues updated between the specified dates for a specific project if provided.
        
        Args:
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD
            project_key: Optional Jira project key (e.g., "PROJ")
            
        Returns:
            List of dictionaries containing issue information
        """
        try:
            # Validate and format dates using utility function
            formatted_start, formatted_end = validate_and_format_dates(start_date, end_date)
            
            # Build JQL query
            project_clause = f'project = "{project_key}" AND ' if project_key else ''
            jql = f'{project_clause}updated >= "{formatted_start}" AND updated < "{formatted_end}" ORDER BY updated DESC'
            
            logger.info(f"Executing JQL query: {jql}")
            
            # Get raw issues data
            raw_issues = self.jira_service.search_issues(jql)
            
            # Process each issue to include additional information
            issues_with_details = []
            for issue in raw_issues:
                try:
                    # Get the full issue to access all fields
                    issue_key = issue["key"]
                    issue_details = self.jira_service.get_issue(issue_key)
                    
                    # Create the issue information dictionary
                    issue_info = {
                        "key": issue_key,
                        "summary": issue_details["summary"],
                        "status": issue_details["status"],
                        "type": issue_details.get("type", "Unknown"),
                        "created_date": issue_details["created_date"],
                        "updated": issue_details["updated"],
                        "updatedDate": dateutil.parser.parse(issue_details["updated"]).strftime("%Y-%m-%d"),
                        "daysSinceCreation": issue_details["daysSinceCreation"],
                        "reporter": issue_details["reporter"],
                        "assignee": issue_details["assignee"],
                        "projectKey": issue_key.split("-")[0],  # Extract project key from issue key
                        "backetKey": issue_details.get("backetKey", "Undefined"),  # Add backetKey information
                        "status_change_date": issue_details.get("status_change_date", None),
                        "daysInCurrentStatus": calculate_days_since_date(issue_details.get("status_change_date", None)) if issue_details.get("status_change_date") else None
                    }
                    
                    issues_with_details.append(issue_info)
                except Exception as e:
                    logger.warning(f"Error processing issue {issue.get('key', 'unknown')}: {str(e)}")
                    continue
                
            return issues_with_details
            
        except ConnectionError as e:
            logger.error(f"Connection error retrieving updated issues: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving updated issues: {str(e)}")
            raise
    
    def get_updated_issues_by_project(self, start_date: str, end_date: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all issues updated between the specified dates, grouped by project.
        
        Args:
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD
            
        Returns:
            Dictionary with project keys as keys and lists of issues as values
        """
        try:
            # Get all updated issues regardless of project
            all_issues = self.get_updated_issues(start_date, end_date)
            
            # Group by project
            grouped_issues = {}
            
            for issue in all_issues:
                project_key = issue["projectKey"]
                project_issues = grouped_issues.get(project_key, [])
                project_issues.append(issue)
                grouped_issues[project_key] = project_issues
                
            # Connect to get project names
            jira = self.jira_service.connect()
            projects = {project.key: project.name for project in jira.projects()}
            
            # Rename keys to include project names
            result = {}
            for project_key, issues in grouped_issues.items():
                project_name = projects.get(project_key, "Unknown")
                result[f"{project_name} ({project_key})"] = issues
                
            return result
        except ConnectionError as e:
            logger.error(f"Connection error retrieving grouped issues: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving grouped issues: {str(e)}")
            raise

# Usage example
if __name__ == "__main__":
    import sys
    from datetime import datetime, timedelta
    
    try:
        report = UpdatedIssuesReport()
        
        # Default to last 7 days if no dates provided
        today = datetime.now()
        default_end_date = today.strftime("%Y-%m-%d")
        default_start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        start_date = default_start_date
        end_date = default_end_date
        
        # Parse command line arguments
        if len(sys.argv) > 1:
            start_date = sys.argv[1]
        if len(sys.argv) > 2:
            end_date = sys.argv[2]
            
        print(f"Retrieving issues updated between {start_date} and {end_date}...")
        
        # Get issues updated between dates, grouped by project
        updated_issues_by_project = report.get_updated_issues_by_project(start_date, end_date)
        
        # Count total issues
        total_issues = sum(len(issues) for issues in updated_issues_by_project.values())
        print(f"Found {total_issues} updated issues across {len(updated_issues_by_project)} projects:")
        
        # Display the results grouped by project
        for project_name, project_issues in updated_issues_by_project.items():
            print(f"\nProject: {project_name} - {len(project_issues)} updated issues:")
            
            # Sort issues by update date, most recent first
            sorted_issues = sorted(project_issues, key=lambda x: x["updated"], reverse=True)
            
            for issue in sorted_issues:
                status_info = f"({issue['status']})"
                if issue.get('daysInCurrentStatus') is not None:
                    if issue.get('daysInCurrentStatus') == 0:
                        status_info = f"({issue['status']} - since today)"
                    else:
                        status_info = f"({issue['status']} - {issue['daysInCurrentStatus']} days)"
                
                print(f"  {issue['key']}: [{issue['type']}] {issue['summary']} {status_info} - "
                      f"Updated: {issue['updatedDate']} - Created: {issue['created_date']} ({issue['daysSinceCreation']} days ago) [{issue['backetKey']}]")
                
        # If a specific project is requested via command line
        if len(sys.argv) > 3:
            project_key = sys.argv[3]
            print(f"\n\nLooking up issues specifically for project: {project_key}")
            project_specific_issues = report.get_updated_issues(start_date, end_date, project_key)
            print(f"Found {len(project_specific_issues)} updated issues for project {project_key}:")
            
            # Sort issues by update date, most recent first
            sorted_issues = sorted(project_specific_issues, key=lambda x: x["updated"], reverse=True)
            
            for issue in sorted_issues:
                status_info = f"({issue['status']})"
                if issue.get('daysInCurrentStatus') is not None:
                    if issue.get('daysInCurrentStatus') == 0:
                        status_info = f"({issue['status']} - since today)"
                    else:
                        status_info = f"({issue['status']} - {issue['daysInCurrentStatus']} days)"
                
                print(f"  {issue['key']}: [{issue['type']}] {issue['summary']} {status_info} - "
                      f"Updated: {issue['updatedDate']} - Created: {issue['created_date']} ({issue['daysSinceCreation']} days ago) [{issue['backetKey']}]")
                
    except Exception as e:
        print(f"Error: {str(e)}")