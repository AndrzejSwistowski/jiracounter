"""
Jira Service module for JiraCounter application.

This module provides functionality to connect to the JIRA server and interact with the Jira API.
It uses the JIRA API token for authentication, with credentials retrieved from the config module.
"""

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
            
            # Cache custom field IDs after successful connection
            self._cache_field_ids()
                
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
            
        Raises:
            ConnectionError: If there's an issue connecting to Jira
            Exception: For other errors retrieving the issue
        """
        if not issue_key:
            logger.error("Issue key cannot be empty")
            raise ValueError("Issue key is required")
            
        jira = self.connect()
        try:
            issue = jira.issue(issue_key)
            
            # Use the dynamically discovered field ID if available
            rodzaj_pracy_field = self.field_ids.get('rodzaj_pracy')
            if rodzaj_pracy_field:
                issue.fields.rodzaj_pracy = getattr(issue.fields, rodzaj_pracy_field, None)
            
            # Get data zmiany statusu field value if available
            data_zmiany_statusu_field = self.field_ids.get('data_zmiany_statusu')
            status_change_date = None
            if data_zmiany_statusu_field:
                status_change_date_raw = getattr(issue.fields, data_zmiany_statusu_field, None)
                if status_change_date_raw:
                    # Parse date if available
                    try:
                        status_change_date = dateutil.parser.parse(status_change_date_raw).strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse 'data zmiany statusu' date: {status_change_date_raw}")
            
            created_date = issue.fields.created
            backet_value, backet_key = self._extract_backet_info(issue)
            
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
                "statusChangeDate": status_change_date,
            }
        except ConnectionError as e:
            logger.error(f"Connection error retrieving issue {issue_key}: {str(e)}")
            raise
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
                    # Get data zmiany statusu field value if available
                    status_change_date = None
                    data_zmiany_statusu_field = self.field_ids.get('data_zmiany_statusu')
                    if data_zmiany_statusu_field:
                        status_change_date_raw = getattr(issue.fields, data_zmiany_statusu_field, None)
                        if status_change_date_raw:
                            try:
                                status_change_date = dateutil.parser.parse(status_change_date_raw).strftime("%Y-%m-%d %H:%M:%S")
                            except (ValueError, TypeError):
                                logger.debug(f"Could not parse 'data zmiany statusu' date: {status_change_date_raw}")
                    
                    all_issues.append({
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "status": issue.fields.status.name,
                        "type": issue.fields.issuetype.name if hasattr(issue.fields, 'issuetype') and issue.fields.issuetype else "Unknown",
                        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                        "statusChangeDate": status_change_date,
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
    
    def _cache_field_ids(self) -> None:
        """Look up and cache custom field IDs for use in Jira operations.
        
        This function populates self.field_ids with the IDs of custom fields
        that are needed for various operations.
        """
        if not self.connected or not self.jira_client:
            logger.warning("Cannot cache field IDs without a connection. Connect first.")
            return
            
        # Look up and cache the "rodzaj pracy" field ID
        rodzaj_pracy_id = self.get_field_id_by_name("rodzaj pracy")
        if rodzaj_pracy_id:
            self.field_ids['rodzaj_pracy'] = rodzaj_pracy_id
            logger.debug(f"Found 'rodzaj pracy' field with ID: {rodzaj_pracy_id}")
        else:
            # Fallback to the ID from config if available
            self.field_ids['rodzaj_pracy'] = config.JIRA_CUSTOM_FIELDS.get('RODZAJ_PRACY')
            logger.debug(f"Using fallback ID for 'rodzaj pracy' field: {self.field_ids['rodzaj_pracy']}")
            
        # Look up and cache the "data zmiany statusu" field ID
        data_zmiany_statusu_id = self.get_field_id_by_name("data zmiany statusu")
        if data_zmiany_statusu_id:
            self.field_ids['data_zmiany_statusu'] = data_zmiany_statusu_id
            logger.debug(f"Found 'data zmiany statusu' field with ID: {data_zmiany_statusu_id}")
        else:
            # Fallback to the ID from config if available
            self.field_ids['data_zmiany_statusu'] = config.JIRA_CUSTOM_FIELDS.get('DATA_ZMIANY_STATUSU')
            logger.debug(f"Using fallback ID for 'data zmiany statusu' field: {self.field_ids['data_zmiany_statusu']}")
    
    def _extract_backet_info(self, issue) -> tuple:
        """Extract backet value and key from the rodzaj_pracy field.
        
        Args:
            issue: Jira issue object
            
        Returns:
            tuple: (backet_value, backet_key)
        """
        backet_value = None
        backet_key = None
        
        if hasattr(issue.fields, 'rodzaj_pracy') and issue.fields.rodzaj_pracy:
            # Check if rodzaj_pracy is a CustomFieldOption object
            if hasattr(issue.fields.rodzaj_pracy, 'value'):
                backet_value = issue.fields.rodzaj_pracy.value
            elif isinstance(issue.fields.rodzaj_pracy, str):
                backet_value = issue.fields.rodzaj_pracy
                
            # Try to extract the key if it has the format "Something [KEY]"
            if backet_value and '[' in backet_value and ']' in backet_value:
                try:
                    backet_key = backet_value.split('[')[1].split(']')[0]
                except (IndexError, AttributeError):
                    logger.debug(f"Could not extract backet key from value: {backet_value}")
        
        return backet_value, backet_key

    def get_issue_changelog(self, issue_key: str) -> List[Dict[str, Any]]:
        """Retrieve the changelog for a specific issue.
        
        Args:
            issue_key: The Jira issue key (e.g., "PROJ-123")
            
        Returns:
            List of changelog entries containing the history of changes
            
        Raises:
            ConnectionError: If there's an issue connecting to Jira
            Exception: For other errors retrieving the changelog
        """
        if not issue_key:
            logger.error("Issue key cannot be empty")
            raise ValueError("Issue key is required")
            
        jira = self.connect()
        try:
            issue = jira.issue(issue_key, expand='changelog')
            
            changelog_entries = []
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
                for history in issue.changelog.histories:
                    author = history.author.displayName if hasattr(history.author, 'displayName') else history.author.name
                    created = history.created
                    
                    changes = []
                    for item in history.items:
                        changes.append({
                            'field': item.field,
                            'fieldtype': item.fieldtype if hasattr(item, 'fieldtype') else None,
                            'from': item.fromString,
                            'to': item.toString
                        })
                    
                    changelog_entries.append({
                        'id': history.id,  # Adding history ID to identify each change
                        'author': author,
                        'created': created,
                        'created_date': dateutil.parser.parse(created).strftime("%Y-%m-%d %H:%M:%S"),
                        'changes': changes
                    })
                
            return changelog_entries
            
        except ConnectionError as e:
            logger.error(f"Connection error retrieving changelog for issue {issue_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving changelog for issue {issue_key}: {str(e)}")
            raise

# Usage example
if __name__ == "__main__":
    try:
        service = JiraService()
        jira = service.connect()

        issue = service.get_issue("PFBP-139")
        change_log = service.get_issue_changelog("PFBP-139")
        days_in_status = calculate_days_since_date(issue.get('statusChangeDate')) if issue.get('statusChangeDate') else "N/A"
        print(f"Issue: {issue['key']} - {issue['summary']} {issue['backetKey']} ({issue['status']} - {days_in_status} days in status) - Created: {issue['creationDate']} ({issue['daysSinceCreation']} days ago) - Reporter: {issue['reporter']} - Assignee: {issue['assignee']}")   
        print(f"Connected to Jira as {config.JIRA_USERNAME}")
        
        # Example: Get a sample project
        projects = jira.projects()
        if projects:
            print(f"Sample project: {projects[0].name} ({projects[0].key})")
    except Exception as e:
        print(f"Error: {str(e)}")