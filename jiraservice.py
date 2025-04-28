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
        self.field_ids = {}
        
    def get_field_id_by_name(self, field_name: str) -> Optional[str]:
        """Find the custom field ID by its visible name.
        
        Args:
            field_name: The visible name of the field in Jira
            
        Returns:
            Optional[str]: The field ID if found, None otherwise
        """
        if not self.connected or not self.jira_client:
            self.connect()
            
        try:
            fields = self.jira_client.fields()
            for field in fields:
                if field['name'].lower() == field_name.lower():
                    logger.debug(f"Found field '{field_name}' with ID: {field['id']}")
                    return field['id']
            
            logger.warning(f"Field '{field_name}' not found in Jira")
            return None
        except Exception as e:
            logger.error(f"Error finding field ID for '{field_name}': {str(e)}")
            return None
        
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
            
            # Look up and cache field IDs after successful connection
            rodzaj_pracy_id = self.get_field_id_by_name("rodzaj pracy")
            if rodzaj_pracy_id:
                self.field_ids['rodzaj_pracy'] = rodzaj_pracy_id
                logger.info(f"Found 'rodzaj pracy' field with ID: {rodzaj_pracy_id}")
            else:
                # Fallback to the ID from config if available
                self.field_ids['rodzaj_pracy'] = config.JIRA_CUSTOM_FIELDS.get('RODZAJ_PRACY')
                logger.info(f"Using fallback ID for 'rodzaj pracy' field: {self.field_ids['rodzaj_pracy']}")
                
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
            
            # Use the dynamically discovered field ID if available
            rodzaj_pracy_field = self.field_ids.get('rodzaj_pracy')
            if rodzaj_pracy_field:
                issue.fields.rodzaj_pracy = getattr(issue.fields, rodzaj_pracy_field, None)
            
            created_date = issue.fields.created
            
            # Handle the rodzaj_pracy field which could be a CustomFieldOption object
            backet_value = None
            backet_key = None
            
            if hasattr(issue.fields, 'rodzaj_pracy') and issue.fields.rodzaj_pracy:
                # Check if rodzaj_pracy is a CustomFieldOption object
                if hasattr(issue.fields.rodzaj_pracy, 'value'):
                    # It's a CustomFieldOption object
                    backet_value = issue.fields.rodzaj_pracy.value
                    # Try to extract the key if it has the format "Something [KEY]"
                    if '[' in backet_value and ']' in backet_value:
                        try:
                            backet_key = backet_value.split('[')[1].split(']')[0]
                        except (IndexError, AttributeError):
                            pass
                elif isinstance(issue.fields.rodzaj_pracy, str):
                    # It's a string
                    backet_value = issue.fields.rodzaj_pracy
                    # Try to extract the key if it has the format "Something [KEY]"
                    if '[' in backet_value and ']' in backet_value:
                        try:
                            backet_key = backet_value.split('[')[1].split(']')[0]
                        except (IndexError, AttributeError):
                            pass
            
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
                "backet": backet_value,
                "backetKey": backet_key,
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

        issue = service.get_issue("PFBP-139")
        print(f"Issue: {issue['key']} - {issue['summary']} {issue['backetKey']} ({issue['status']}) - Created: {issue['creationDate']} ({issue['daysSinceCreation']} days ago) - Reporter: {issue['reporter']} - Assignee: {issue['assignee']}")   
        print(f"Connected to Jira as {config.JIRA_USERNAME}")
        
        # Example: Get a sample project
        projects = jira.projects()
        if projects:
            print(f"Sample project: {projects[0].name} ({projects[0].key})")
    except Exception as e:
        print(f"Error: {str(e)}")