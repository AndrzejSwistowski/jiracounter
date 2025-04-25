#class returs list 
# and Type = Epic AND status NOT IN (Done, Canceled, Closed, Completed )
# has metods get all projects and get returns epics of requested project
# epic information contains:
#     # - idIssue
#     # - summary
#     # - status
			# - creation 
#     # - numers of days from creation to now

import logging
from typing import List, Dict, Any
from datetime import datetime
import dateutil.parser
from jiraservice import JiraService

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
            raw_epics = self.jira_service.search_issues(jql, max_results=100)
            
            # Process each epic to include additional information
            epics_with_details = []
            for epic in raw_epics:
                try:
                    # Get the full issue to access all fields
                    issue_key = epic["key"]
                    issue_details = self.jira_service.get_issue(issue_key)
                    
                    # Parse the creation date using dateutil for more robust parsing
                    try:
                        creation_date = dateutil.parser.parse(issue_details["created"])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing creation date for {issue_key}: {str(e)}")
                        creation_date = datetime.now().astimezone()
                    
                    # Calculate days since creation
                    days_since_creation = (datetime.now().astimezone() - creation_date).days
                    
                    # Create the epic information dictionary
                    epic_info = {
                        "idIssue": issue_key,
                        "summary": issue_details["summary"],
                        "status": issue_details["status"],
                        "creation": creation_date.strftime("%Y-%m-%d"),
                        "daysSinceCreation": days_since_creation
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
                try:
                    epics = self.get_epics_for_project(project_key)
                    if epics:  # Only include projects that have open epics
                        all_epics[project_key] = epics
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
        
        # Connect to Jira to get projects directly
        jira = report.jira_service.connect()
        projects = jira.projects()
        
        print("Available Projects:")
        for project in projects:
            print(f"  {project.key}: {project.name}")
            
        # Example: Get epics for a specific project
        if projects:
            example_project = projects[2].key
            print(f"\nEpics for project {example_project}:")
            epics = report.get_epics_for_project(example_project)
            for epic in epics:
                print(f"  {epic['idIssue']}: {epic['summary']} ({epic['status']}) - Created: {epic['creation']} ({epic['daysSinceCreation']} days ago)")
                
        # Example: Get epics for all projects
        print("\nAll epics for all projects:")
        all_epics = report.get_epics_for_all_projects()
        for project_key, project_epics in all_epics.items():
            print(f"\nProject: {project_key}")
            for epic in project_epics:
                print(f"  {epic['idIssue']}: {epic['summary']} ({epic['status']}) - Created: {epic['creation']} ({epic['daysSinceCreation']} days ago)")
    except Exception as e:
        print(f"Error: {str(e)}")
