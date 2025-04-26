#class returs list 
# and Type = Epic AND status NOT IN (Done, Canceled, Closed, Completed )
# has metods get all projects and get returns epics of requested project
# epic information contains:
#     # - idIssue
#     # - summary
#     # - status
			# - creationDate 
#     # - numers of days from creation to now

import logging
from typing import List, Dict, Any
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
            raw_epics = self.jira_service.search_issues(jql)
            
            # Process each epic to include additional information
            epics_with_details = []
            for epic in raw_epics:
                try:
                    # Get the full issue to access all fields
                    issue_key = epic["key"]
                    issue_details = self.jira_service.get_issue(issue_key)
                    
                    # Create the epic information dictionary
                    epic_info = {
                        "idIssue": issue_key,
                        "summary": issue_details["summary"],
                        "status": issue_details["status"],
                        "creationDate": issue_details["creationDate"],
                        "daysSinceCreation": issue_details["daysSinceCreation"],
                        "Reporter": issue_details["reporter"],
                        "Assignee": issue_details["assignee"],
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
                        all_epics[f"{project_name}({project_key})"] = epics
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
        for project_key, project_epics in all_epics.items():
            print(f"\nProject: {project_key} ")
            for epic in project_epics:
                print(f"  {epic['idIssue']}: {epic['summary']} ({epic['status']}) - Created: {epic['creationDate']} ({epic['daysSinceCreation']} days ago) - Reporter: {epic['Reporter']} - Assignee: {epic['Assignee']}")
    except Exception as e:
        print(f"Error: {str(e)}")
