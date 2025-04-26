#function that connects to the JIRA server and returns a JIRA object
# using the JIRA API token for authentication.
# credentials are retrieved from the config module.

import logging
from typing import Optional, Dict, List, Any
from jira import JIRA
import config
import dateutil.parser
from datetime import datetime
from utils import calculate_days_since_date

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class JiraService:
    """Service class to interact with Jira API."""
    
    def __init__(self):
        """Initialize the Jira service."""
        self.jira_client = None
        self.connected = False
        
    def connect(self) -> JIRA:
        """Connect to the Jira server using credentials from config.
        
        Returns:
            JIRA: A connected JIRA client object.
            
        Raises:
            ConnectionError: If connection fails.
        """
        if self.connected and self.jira_client:
            return self.jira_client
            
        try:
            username, token = config.get_credentials()
            
            if not token:
                logger.error("Jira API token not provided. Please set the JIRA_API_TOKEN environment variable.")
                raise ValueError("Jira API token is required")
                
            logger.info(f"Connecting to Jira at {config.JIRA_BASE_URL}")
            self.jira_client = JIRA(
                server=config.JIRA_BASE_URL,
                basic_auth=(username, token)
            )
            self.connected = True
            logger.info("Successfully connected to Jira")
            return self.jira_client
            
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {str(e)}")
            self.connected = False
            raise ConnectionError(f"Could not connect to Jira: {str(e)}")
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Retrieve an issue by its key.
        
        Args:
            issue_key: The Jira issue key (e.g., "PROJ-123")
            
        Returns:
            Dict containing the issue details
        """
        jira = self.connect()
        try:
            issue = jira.issue(issue_key)
            created_date = issue.fields.created
            
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "type": issue.fields.issuetype.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "created": created_date,
                "creationDate": dateutil.parser.parse(created_date).strftime("%Y-%m-%d"),
                "daysSinceCreation": calculate_days_since_date(created_date),
                "updated": issue.fields.updated,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
            }
        except Exception as e:
            logger.error(f"Error retrieving issue {issue_key}: {str(e)}")
            raise

    def search_issues(self, jql_query: str) -> List[Dict[str, Any]]:
        """Search for issues using JQL with automatic pagination.
        
        Args:
            jql_query: JQL query string
            
        Returns:
            List of issues matching the query (up to 1000 results)
        """
        jira = self.connect()
        all_issues = []
        max_allowed_results = 1000
        
        try:
            # JIRA API typically limits each request to 100 items
            page_size = 100
            start_at = 0
            
            while len(all_issues) < max_allowed_results:
                # Fetch the current page of results
                logger.debug(f"Fetching issues starting at {start_at} with page size {page_size}")
                issues_page = jira.search_issues(
                    jql_query, 
                    startAt=start_at, 
                    maxResults=page_size
                )
                
                # If no more results, break the loop
                if len(issues_page) == 0:
                    break
                    
                # Process and add the current page results
                for issue in issues_page:
                    all_issues.append({
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "status": issue.fields.status.name,
                        "type": issue.fields.issuetype.name if hasattr(issue.fields, 'issuetype') and issue.fields.issuetype else "Unknown",
                        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                    })
                
                # If we got fewer results than requested, there are no more results
                if len(issues_page) < page_size:
                    break
                    
                # Update the starting point for the next iteration
                start_at += len(issues_page)
                
                # Check if we've reached the maximum allowed total
                if len(all_issues) >= max_allowed_results:
                    logger.warning(f"Reached maximum result limit of {max_allowed_results} records. Some results may be omitted.")
                    break
                
            return all_issues
            
        except Exception as e:
            logger.error(f"Error searching issues with query {jql_query}: {str(e)}")
            raise

# Usage example
if __name__ == "__main__":
    try:
        service = JiraService()
        jira = service.connect()
        print(f"Connected to Jira as {config.JIRA_USERNAME}")
        
        # Example: Get a sample project
        projects = jira.projects()
        if projects:
            print(f"Sample project: {projects[0].name} ({projects[0].key})")
    except Exception as e:
        print(f"Error: {str(e)}")