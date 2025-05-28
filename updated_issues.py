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
from utils import calculate_days_since_date, validate_and_format_dates, format_date_polish
from time_utils import format_working_minutes_to_text, calculate_working_minutes_since_date

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

class UpdatedIssuesReport:
    """Service class to retrieve information about issues updated between specific dates in Jira projects."""
    
    def __init__(self):
        """Initialize the Updated Issues Report service."""
        self.jira_service = JiraService()
    
    def get_updated_issues(self, from_date: str, to_date: str, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all issues updated between the specified dates.
        
        Args:
            from_date: The start date in format YYYY-MM-DD
            to_date: The end date in format YYYY-MM-DD
            project_key: Optional project key to filter issues by project
            
        Returns:
            List of dictionaries containing issue information
        """
        try:
            # Validate and format the dates
            from_date_formatted, to_date_formatted = validate_and_format_dates(from_date, to_date)
            
            # Build JQL query based on parameters
            jql_parts = [f'updated >= "{from_date_formatted}" AND updated <= "{to_date_formatted}"']
            
            if project_key:
                jql_parts.append(f'project = "{project_key}"')
                
            jql = ' AND '.join(jql_parts) + ' ORDER BY updated DESC'
            
            # Get raw issues data
            raw_issues = self.jira_service.search_issues(jql)
            
            # Process each issue to include additional information
            issues_with_details = []
            for issue_details in raw_issues:
                try:
                    # Get the full issue to access all fields
                    issue_key = issue_details["key"]
                    #issue_details = self.jira_service.get_issue(issue_key)
                      # Calculate minutes since update
                    updated_date = dateutil.parser.parse(issue_details["updated"])
                    minutes_since_update = int((datetime.now(updated_date.tzinfo) - updated_date).total_seconds() / 60)
                    
                    # Create the issue information dictionary
                    issue_info = {
                        "key": issue_key,
                        "summary": issue_details["summary"],
                        "status": issue_details["status"],
                        "type": issue_details["type"],
                        "project": issue_details["project"],                        "updated": issue_details["updated"],
                        "minutes_since_update": minutes_since_update,
                        "created": issue_details["created"],
                        "minutes_since_creation": issue_details["minutes_since_creation"],
                        "reporter": issue_details["reporter"],
                        "assignee": issue_details["assignee"],                        "allocation_code": issue_details.get("allocation_code", "Undefined"),
                        "status_change_date": issue_details.get("status_change_date", None),
                        "minutes_in_current_status": calculate_working_minutes_since_date(issue_details.get("status_change_date", None)) if issue_details.get("status_change_date") else None
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
    
    def get_issues_by_project(self, from_date: str, to_date: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all issues updated between specified dates, grouped by project.
        
        Args:
            from_date: The start date in format YYYY-MM-DD
            to_date: The end date in format YYYY-MM-DD
            
        Returns:
            Dictionary with project keys as keys and lists of issues as values
        """
        try:
            # Get all updated issues
            all_issues = self.get_updated_issues(from_date, to_date)
            
            # Group issues by project
            issues_by_project = {}
            for issue in all_issues:
                project_key = issue["project"]
                
                if project_key not in issues_by_project:
                    issues_by_project[project_key] = []
                    
                issues_by_project[project_key].append(issue)
                    
            return issues_by_project
        except Exception as e:
            logger.error(f"Error grouping updated issues by project: {str(e)}")
            raise

# Usage example
if __name__ == "__main__":
    try:
        from datetime import datetime, timedelta
        
        # Default: get issues updated in the last 1 days
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Parse command line arguments for date range if provided
        import sys
        if len(sys.argv) > 2:
            week_ago = sys.argv[1]
            today = sys.argv[2]
        
        print(f"Retrieving issues updated between {week_ago} and {today}")
        
        report = UpdatedIssuesReport()
        issues_by_project = report.get_issues_by_project(week_ago, today)
          # Display the results
        total_issues = sum(len(issues) for issues in issues_by_project.values())
        print(f"Found {total_issues} updated issues across {len(issues_by_project)} projects:")
        
        for project_key, project_issues in issues_by_project.items():
            print(f"\nProject: {project_key} - {len(project_issues)} updated issues:")
            for issue in project_issues:
                status_info = f"({issue['status']})"
                if issue.get('minutes_in_current_status') is not None:
                    if issue.get('minutes_in_current_status') == 0:
                        status_info = f"({issue['status']} - since today)"
                    else:
                        formatted_time = format_working_minutes_to_text(issue['minutes_in_current_status'])
                        status_info = f"({issue['status']} - {formatted_time})"
                          # Format the dates in Polish
                updated_date_polish = format_date_polish(issue['updated'])
                created_date_polish = format_date_polish(issue['created'])
                  # Convert minutes to human-readable format
                time_ago = format_working_minutes_to_text(issue.get('minutes_since_creation'))
                time_ago_display = time_ago if time_ago else "N/A"
                
                print(f"  {issue['key']}: [{issue['type']}] {issue['summary']} {status_info} - "
                      f"Updated: {updated_date_polish} - Created: {created_date_polish} ({time_ago_display} ago) [{issue['allocation_code']}]")
                
    except Exception as e:
        print(f"Error: {str(e)}")
