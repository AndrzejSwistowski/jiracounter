"""
Epic Opened Report module for JiraCounter application.

This module contains functionality to retrieve information about open epics
from Jira projects. It can report on epics that are not in Done, Canceled,
Closed, or Completed status. The epic information includes:
- Issue ID
- Summary
- Status
- Creation date
- Number of days from creation to now
- Reporter
- Assignee
"""

import logging
from typing import List, Dict, Any
from jiraservice import JiraService
from utils import calculate_days_since_date, format_date_polish
from time_utils import format_working_minutes_to_text, calculate_working_minutes_since_date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EpicOpenedReport:
    """Service class to retrieve information about open epics in Jira projects."""
    
    def __init__(self):
        """Initialize the Epic Report service."""
        self.jira_service = JiraService()
    
    def get_epics_for_project(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all open epics for a specific project.
        
        Args:
            project_key: The Jira project key (e.g., "PROJ")
            
        Returns:
            List of dictionaries containing epic information
        """
        try:
            # JQL query to find all issues of type "Epic" in the specified project that are not closed
            jql = f'project = "{project_key}" AND Type = Epic AND status NOT IN (Done, Canceled, Closed, Completed) ORDER BY created DESC'
            
            # Get raw issues data
            raw_epics = self.jira_service.search_issues(jql)
            
            # Process each epic to include additional information
            epics_with_details = []
            for issue_details in raw_epics:
                try:
                    # Get the full issue to access all fields
                    issue_key = issue_details["key"]
                    #issue_details = self.jira_service.get_issue(issue_key)
                    
                    # Create the epic information dictionary
                    epic_info = {
                        "idIssue": issue_key,
                        "summary": issue_details["summary"],
                        "allocation_code": issue_details.get("allocation_code", None),
                        "status": issue_details["status"],
                        "created": issue_details["created"],
                        "minutes_since_creation": issue_details.get("minutes_since_creation", None),
                        "Reporter": issue_details.get("reporter_display_name", None),
                        "Assignee": issue_details.get("assignee_display_name", None),
                        "status_change_date": issue_details.get("status_change_date", None),
                        "minutes_in_current_status": calculate_working_minutes_since_date(issue_details.get("status_change_date", None)) if issue_details.get("status_change_date") else None,
                    }
                    
                    epics_with_details.append(epic_info)
                except Exception as e:
                    logger.warning(f"Error processing epic {epic.get('key', 'unknown')}: {str(e)}")
                    continue
                
            return epics_with_details
            
        except ConnectionError as e:
            logger.error(f"Connection error retrieving epics for project {project_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving epics for project {project_key}: {str(e)}")
            raise

    def get_epics_for_all_projects(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all open epics for all available projects.
        
        Returns:
            Dictionary with project keys as keys and lists of epics as values
        """
        try:
            # Connect to Jira service and get projects directly
            jira = self.jira_service.connect()
            projects = jira.projects()
            
            all_epics = {}
            
            for project in projects:
                project_key = project.key
                project_name = project.name
                try:
                    epics = self.get_epics_for_project(project_key)
                    if epics:  # Only include projects that have open epics
                        all_epics[(project_key, project_name)] = epics
                except Exception as e:
                    logger.warning(f"Error retrieving epics for project {project_key}: {str(e)}. Skipping.")
                    
            return all_epics
        except ConnectionError as e:
            logger.error(f"Connection error retrieving epics for all projects: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving epics for all projects: {str(e)}")
            raise

# Usage example
if __name__ == "__main__":
    try:
        report = EpicOpenedReport()
        
        jira = report.jira_service.connect()
        all_epics = report.get_epics_for_all_projects()
        for (project_key, project_name), project_epics in all_epics.items():
            print(f"\nProject: {project_name} ({project_key})")
            for epic in project_epics:
                status_info = f"{epic['status']}"
                if epic.get('minutes_in_current_status') is not None:
                    formatted_time = format_working_minutes_to_text(epic['minutes_in_current_status'])
                    if formatted_time:
                        status_info += f" - {formatted_time} in current status"
                        
                # Format the creation date in Polish
                created_date_polish = format_date_polish(epic['created'])
                
                # Convert minutes to human-readable format
                time_ago = format_working_minutes_to_text(epic.get('minutes_since_creation'))
                time_ago_display = time_ago if time_ago else "N/A"
                
                print(f"  {epic['idIssue']}: {epic['allocation_code']} {epic['summary']}  ({status_info}) - Created: {created_date_polish} ({time_ago_display} ago) - Reporter: {epic['Reporter']} - Assignee: {epic['Assignee']}")
    except Exception as e:
        print(f"Error: {str(e)}")
