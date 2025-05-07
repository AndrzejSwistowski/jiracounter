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
from datetime import datetime, timedelta
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
    
    def _extract_issue_data(self, issue) -> Dict[str, Any]:
        """Extract common issue data into a standardized dictionary.
        
        Args:
            issue: Jira issue object
            
        Returns:
            Dict containing the standardized issue details
        """
        # Set rodzaj_pracy field if available
        rodzaj_pracy_field = self.field_ids.get('rodzaj_pracy')
        if rodzaj_pracy_field:
            issue.fields.rodzaj_pracy = getattr(issue.fields, rodzaj_pracy_field, None)
        
        # Extract backet information
        backet_value, backet_key = self._extract_backet_info(issue)
        
        # Extract status change date if available
        status_change_date = None
        data_zmiany_statusu_field = self.field_ids.get('data_zmiany_statusu')
        if data_zmiany_statusu_field:
            status_change_date_raw = getattr(issue.fields, data_zmiany_statusu_field, None)
            if status_change_date_raw:
                try:
                    status_change_date = dateutil.parser.parse(status_change_date_raw).strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse 'data zmiany statusu' date: {status_change_date_raw}")
        
        # Extract component information
        components = []
        if hasattr(issue.fields, 'components') and issue.fields.components:
            for component in issue.fields.components:
                comp_info = {
                    "id": component.id,
                    "name": component.name
                }
                # Add description if available
                if hasattr(component, 'description') and component.description:
                    comp_info["description"] = component.description
                components.append(comp_info)
        
        # Extract labels
        labels = []
        if hasattr(issue.fields, 'labels') and issue.fields.labels:
            labels = issue.fields.labels
            
        # Extract basic issue data
        issue_data = {
            "id": issue.id,
            "key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "type": issue.fields.issuetype.name if hasattr(issue.fields, 'issuetype') and issue.fields.issuetype else "Unknown",
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
            "statusChangeDate": status_change_date,
            "components": components,
            "labels": labels,
            "reporter": issue.fields.reporter.displayName if hasattr(issue.fields, 'reporter') and issue.fields.reporter else None,
            "backet": backet_value,
            "backetKey": backet_key,
        }
        
        return issue_data

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
            
            # Extract common issue data (including rodzaj_pracy and backet info)
            issue_data = self._extract_issue_data(issue)
            
            # Add fields specific to get_issue method
            created_date = issue.fields.created
            
            issue_data.update({
                "created": created_date,
                "creationDate": dateutil.parser.parse(created_date).strftime("%Y-%m-%d"),
                "daysSinceCreation": calculate_days_since_date(created_date),
                "updated": issue.fields.updated,
            })
                    
            return issue_data
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
                    # Extract standardized issue data 
                    issue_data = self._extract_issue_data(issue)
                    all_issues.append(issue_data)
                
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

    def get_issue_history(self, start_date=None, end_date=None, max_issues=None) -> List[Dict[str, Any]]:
        """Retrieve issue history records for issues updated within a date range.
        
        This method retrieves issues updated within the specified date range and
        extracts their changelog entries for storage in a data warehouse or
        Elasticsearch index.
        
        Args:
            start_date: The start date for the search (datetime or str)
            end_date: The end date for the search (datetime or str)
            max_issues: Maximum number of issues to process
            
        Returns:
            List of history records with standardized format
        """
        jira = self.connect()
        
        # Format dates for JQL
        if start_date:
            if isinstance(start_date, datetime):
                start_str = start_date.strftime("%Y-%m-%d %H:%M")
            else:
                start_str = str(start_date)
        else:
            # Default to 7 days ago if no start date provided
            start_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M")
            
        if end_date:
            if isinstance(end_date, datetime):
                end_str = end_date.strftime("%Y-%m-%d %H:%M")
            else:
                end_str = str(end_date)
        else:
            end_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
        logger.info(f"Retrieving issues updated between {start_str} and {end_str}")
        
        # Build JQL query for issues updated in the date range
        jql = f'updated >= "{start_str}" AND updated <= "{end_str}" ORDER BY updated ASC'
        
        try:
            # Get all issues updated in the date range
            all_issues = []
            
            # JIRA API typically limits each request to 100 items
            page_size = 100
            start_at = 0
            
            while True:
                # Fetch the current page of results
                logger.debug(f"Fetching issues starting at {start_at} with page size {page_size}")
                issues_page = jira.search_issues(
                    jql, 
                    startAt=start_at, 
                    maxResults=page_size,
                    fields="key,issuetype,status,project,summary,assignee,reporter,created,updated"
                )
                
                # If no more results, break the loop
                if len(issues_page) == 0:
                    break
                    
                # Add the issues to our list
                all_issues.extend(issues_page)
                
                # If we got fewer results than requested, there are no more results
                if len(issues_page) < page_size:
                    break
                    
                # Update the starting point for the next iteration
                start_at += len(issues_page)
                
                # Check if we've reached the maximum allowed total
                if max_issues and len(all_issues) >= max_issues:
                    logger.info(f"Reached maximum issue limit of {max_issues}.")
                    break
            
            logger.info(f"Found {len(all_issues)} issues updated in the specified date range")
            
            # Process each issue to extract history records
            all_history_records = []
            
            for issue in all_issues:
                issue_key = issue.key
                logger.debug(f"Processing changelog for issue {issue_key}")
                
                # Get the issue with expanded changelog
                issue_with_changelog = jira.issue(issue_key, expand="changelog")
                
                # Extract basic issue information
                issue_type = issue.fields.issuetype.name
                status_name = issue.fields.status.name
                project_key = issue.fields.project.key
                project_name = issue.fields.project.name
                
                # Extract assignee and reporter information
                assignee_username = None
                assignee_display = None
                if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                    assignee_username = issue.fields.assignee.name if hasattr(issue.fields.assignee, 'name') else issue.fields.assignee.accountId
                    assignee_display = issue.fields.assignee.displayName if hasattr(issue.fields.assignee, 'displayName') else None
                
                reporter_username = None
                reporter_display = None
                if hasattr(issue.fields, 'reporter') and issue.fields.reporter:
                    reporter_username = issue.fields.reporter.name if hasattr(issue.fields.reporter, 'name') else issue.fields.reporter.accountId
                    reporter_display = issue.fields.reporter.displayName if hasattr(issue.fields.reporter, 'displayName') else None
                
                # Extract parent issue key if this is a subtask
                parent_key = None
                if hasattr(issue.fields, 'parent'):
                    parent_key = issue.fields.parent.key
                
                # Extract allocation information
                allocation_code = None
                if hasattr(issue.fields, 'rodzaj_pracy') and issue.fields.rodzaj_pracy:
                    backet_value, backet_key = self._extract_backet_info(issue)
                    allocation_code = backet_key
                
                # Process creation record
                created_date = dateutil.parser.parse(issue.fields.created)
                
                # Create a history record for the issue creation
                creation_record = {
                    'historyId': int(f"{issue.id}00000"),  # Use a synthetic ID for creation
                    'historyDate': created_date,
                    'factType': 0,  # 0 = create
                    'issueId': issue.id,
                    'issueKey': issue_key,
                    'typeName': issue_type,
                    'statusName': 'Open',  # Assume issues start as Open
                    'assigneeUserName': assignee_username,
                    'assigneeDisplayName': assignee_display,
                    'reporterUserName': reporter_username,
                    'reporterDisplayName': reporter_display,
                    'allocationCode': allocation_code,
                    'projectKey': project_key,
                    'projectName': project_name,
                    'parentKey': parent_key,
                    'authorUserName': reporter_username,
                    'authorDisplayName': reporter_display,
                    'changes': []
                }
                
                # Only add creation record if it's within our date range
                if start_date is None or created_date >= start_date:
                    all_history_records.append(creation_record)
                
                # Process changelog entries
                if hasattr(issue_with_changelog, 'changelog') and hasattr(issue_with_changelog.changelog, 'histories'):
                    for history in issue_with_changelog.changelog.histories:
                        history_date = dateutil.parser.parse(history.created)
                        
                        # Skip records outside our date range
                        if (start_date and history_date < start_date) or (end_date and history_date > end_date):
                            continue
                            
                        # Determine fact type (default to update)
                        fact_type = 3  # 3 = update
                        
                        # Check if this is a status change
                        changes = []
                        for item in history.items:
                            changes.append({
                                'field': item.field,
                                'from': item.fromString,
                                'to': item.toString
                            })
                            
                            if item.field == 'status':
                                fact_type = 2  # 2 = transition
                        
                        # Get author information
                        author_username = history.author.name if hasattr(history.author, 'name') else history.author.accountId
                        author_display = history.author.displayName if hasattr(history.author, 'displayName') else None
                        
                        # Create a history record
                        history_record = {
                            'historyId': int(history.id),
                            'historyDate': history_date,
                            'factType': fact_type,
                            'issueId': issue.id,
                            'issueKey': issue_key,
                            'typeName': issue_type,
                            'statusName': status_name,
                            'assigneeUserName': assignee_username,
                            'assigneeDisplayName': assignee_display,
                            'reporterUserName': reporter_username,
                            'reporterDisplayName': reporter_display,
                            'allocationCode': allocation_code,
                            'projectKey': project_key,
                            'projectName': project_name,
                            'parentKey': parent_key,
                            'authorUserName': author_username,
                            'authorDisplayName': author_display,
                            'changes': changes
                        }
                        
                        all_history_records.append(history_record)
            
            # Sort by history date
            all_history_records.sort(key=lambda x: x['historyDate'])
            
            logger.info(f"Extracted {len(all_history_records)} history records")
            return all_history_records
            
        except Exception as e:
            logger.error(f"Error retrieving issue history: {str(e)}")
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