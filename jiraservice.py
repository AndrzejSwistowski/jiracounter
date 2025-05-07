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
        
        # Extract parent issue information
        parent_issue = None
        if hasattr(issue.fields, 'parent'):
            parent_issue = {
                "id": issue.fields.parent.id,
                "key": issue.fields.parent.key,
                "summary": getattr(issue.fields.parent, 'summary', None)
            }
        
        # Extract epic information
        epic_issue = None
        epic_link_field = self.field_ids.get('epic_link')
        if epic_link_field:
            epic_key = getattr(issue.fields, epic_link_field, None)
            if epic_key:
                try:
                    # Try to get the epic issue
                    epic = self.jira_client.issue(epic_key)
                    epic_issue = {
                        "id": epic.id,
                        "key": epic.key,
                        "summary": epic.fields.summary
                    }
                except Exception as e:
                    logger.debug(f"Error retrieving epic issue {epic_key}: {e}")
        
        # If no epic found but there is a parent, try to get the parent's epic
        if not epic_issue and parent_issue:
            try:
                # Get parent issue with its epic link
                parent = self.jira_client.issue(parent_issue["key"])
                
                # Check if parent has an epic
                if epic_link_field and hasattr(parent.fields, epic_link_field):
                    parent_epic_key = getattr(parent.fields, epic_link_field)
                    if parent_epic_key:
                        try:
                            # Get the parent's epic
                            parent_epic = self.jira_client.issue(parent_epic_key)
                            epic_issue = {
                                "id": parent_epic.id,
                                "key": parent_epic.key,
                                "summary": parent_epic.fields.summary,
                                "inherited": True  # Mark as inherited from parent
                            }
                            logger.debug(f"Issue {issue.key} inherited epic {parent_epic_key} from parent {parent_issue['key']}")
                        except Exception as e:
                            logger.debug(f"Error retrieving parent's epic {parent_epic_key}: {e}")
            except Exception as e:
                logger.debug(f"Error retrieving parent issue to check for epic: {e}")
            
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
            "parent_issue": parent_issue,
            "epic_issue": epic_issue
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
            
        # Look up and cache the Epic Link field ID
        epic_link_id = self.get_field_id_by_name("Epic Link")
        if epic_link_id:
            self.field_ids['epic_link'] = epic_link_id
            logger.debug(f"Found 'Epic Link' field with ID: {epic_link_id}")
        else:
            # Fallback to the ID from config if available
            self.field_ids['epic_link'] = config.JIRA_CUSTOM_FIELDS.get('EPIC_LINK')
            logger.debug(f"Using fallback ID for 'Epic Link' field: {self.field_ids['epic_link']}")
    
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
                
                # Extract basic issue information using the existing method
                issue_data = self._extract_issue_data(issue_with_changelog)
                
                # Extract fields we need for the history record
                issue_type = issue_data['type']
                status_name = issue_data['status']
                project_key = issue_data['projectKey'] if 'projectKey' in issue_data else issue.fields.project.key
                project_name = issue_data['projectName'] if 'projectName' in issue_data else issue.fields.project.name
                summary = issue_data['summary']
                labels = issue_data['labels']
                components = issue_data['components']
                allocation_code = issue_data.get('backetKey')
                parent_key = issue_data.get('parentKey')
                
                # Process issue's changelog to extract additional time-based information
                issue_creation_date = dateutil.parser.parse(issue.fields.created)
                current_date = datetime.now(issue_creation_date.tzinfo)
                
                # Import utility functions for working days calculations
                from utils import calculate_working_days_between, find_status_change_date, find_first_status_change_date
                
                # Calculate working days since creation
                working_days_from_creation = calculate_working_days_between(issue_creation_date, current_date)
                
                # Find when the issue entered its current status
                status_change_date = None
                status_change_history = []
                working_days_in_status = None
                
                if hasattr(issue_with_changelog, 'changelog') and hasattr(issue_with_changelog.changelog, 'histories'):
                    histories = list(issue_with_changelog.changelog.histories)
                    for history in histories:
                        for item in history.items:
                            if item.field == 'status' and item.toString == status_name:
                                status_change_date = dateutil.parser.parse(history.created)
                                break
                        if status_change_date:
                            break
                
                    # If we found a status change date, calculate working days in status
                    if status_change_date:
                        working_days_in_status = calculate_working_days_between(status_change_date, current_date)
                    
                    # Extract all changelog entries for further analysis
                    for history in histories:
                        history_date = dateutil.parser.parse(history.created)
                        changes = []
                        for item in history.items:
                            changes.append({
                                'field': item.field,
                                'from': item.fromString,
                                'to': item.toString
                            })
                        status_change_history.append({
                            'historyDate': history_date,
                            'changes': changes
                        })
                
                # Find when the issue moved out of To Do (or equivalent starting status)
                todo_exit_date = find_first_status_change_date(status_change_history)
                working_days_from_todo = None
                if todo_exit_date:
                    working_days_from_todo = calculate_working_days_between(todo_exit_date, current_date)
                
                # Process creation record
                created_date = dateutil.parser.parse(issue.fields.created)
                
                # Ensure both dates are timezone-aware or naive for comparison
                if start_date and start_date.tzinfo is None and created_date.tzinfo is not None:
                    # Make start_date timezone-aware by assigning the same timezone as created_date
                    start_date = start_date.replace(tzinfo=created_date.tzinfo)
                elif start_date and start_date.tzinfo is not None and created_date.tzinfo is None:
                    # Make created_date timezone-aware by assigning the same timezone as start_date
                    created_date = created_date.replace(tzinfo=start_date.tzinfo)
                
                # Create a history record for the issue creation
                creation_record = {
                    'historyId': int(f"{issue.id}00000"),  # Use a synthetic ID for creation
                    'historyDate': created_date,
                    'factType': 0,  # 0 = create
                    'issueId': issue.id,
                    'issueKey': issue_key,
                    'typeName': issue_type,
                    'statusName': 'Open',  # Assume issues start as Open
                    'assigneeUserName': issue_data['assignee'],
                    'assigneeDisplayName': issue_data['assignee'],
                    'reporterUserName': issue_data['reporter'],
                    'reporterDisplayName': issue_data['reporter'],
                    'allocationCode': allocation_code,
                    'projectKey': project_key,
                    'projectName': project_name,
                    'parentKey': parent_key,
                    'authorUserName': issue_data['reporter'],
                    'authorDisplayName': issue_data['reporter'],
                    'changes': [],
                    'summary': summary,
                    'labels': labels,
                    'components': components,
                    'parent_issue': issue_data.get('parent_issue'),
                    'epic_issue': issue_data.get('epic_issue'),
                    'workingDaysFromCreation': 0,  # Just created, so 0 days
                    'workingDaysInStatus': 0,      # Just created, so 0 days in status
                    'workingDaysFromMove': None    # No status change yet
                }
                
                # Only add creation record if it's within our date range
                if start_date is None or created_date >= start_date:
                    all_history_records.append(creation_record)
                
                # Process changelog entries
                if hasattr(issue_with_changelog, 'changelog') and hasattr(issue_with_changelog.changelog, 'histories'):
                    for history in issue_with_changelog.changelog.histories:
                        # Make sure dates have consistent timezone info for comparison
                        history_date = dateutil.parser.parse(history.created)
                        
                        # Default variable initializations
                        start_date_comp = None
                        end_date_comp = None
                        history_date_comp_start = history_date
                        history_date_comp_end = history_date
                        
                        # Handle timezone differences for comparison with start_date
                        if start_date:
                            if start_date.tzinfo is None and history_date.tzinfo is not None:
                                start_date_comp = start_date.replace(tzinfo=history_date.tzinfo)
                            elif start_date.tzinfo is not None and history_date.tzinfo is None:
                                history_date_comp_start = history_date.replace(tzinfo=start_date.tzinfo)
                            else:
                                start_date_comp = start_date
                            
                        # Handle timezone differences for comparison with end_date
                        if end_date:
                            if end_date.tzinfo is None and history_date.tzinfo is not None:
                                end_date_comp = end_date.replace(tzinfo=history_date.tzinfo)
                            elif end_date.tzinfo is not None and history_date.tzinfo is None:
                                history_date_comp_end = history_date.replace(tzinfo=end_date.tzinfo)
                            else:
                                end_date_comp = end_date
                        
                        # Skip records outside our date range
                        if (start_date_comp and history_date_comp_start < start_date_comp) or (end_date_comp and history_date_comp_end > end_date_comp):
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
                        
                        # Calculate time-based metrics as of this history point
                        working_days_from_creation_at_point = calculate_working_days_between(issue_creation_date, history_date)
                        
                        # For each history point, determine how long it had been in the current status
                        status_in_this_history = status_name  # Default to current status
                        working_days_in_status_at_point = working_days_in_status
                        
                        # Check if this history changes the status
                        for change in changes:
                            if change['field'] == 'status':
                                # If this is a status change, find how long it was in the previous status
                                previous_status_change = find_status_change_date(status_change_history, change['from'], None)
                                if previous_status_change:
                                    working_days_in_status_at_point = calculate_working_days_between(previous_status_change, history_date)
                                status_in_this_history = change['to']
                                break
                                
                        # Calculate working days from first status change at this history point
                        working_days_from_move_at_point = None
                        if todo_exit_date and history_date >= todo_exit_date:
                            working_days_from_move_at_point = calculate_working_days_between(todo_exit_date, history_date)
                        
                        # Create a history record
                        history_record = {
                            'historyId': int(history.id),
                            'historyDate': history_date,
                            'factType': fact_type,
                            'issueId': issue.id,
                            'issueKey': issue_key,
                            'typeName': issue_type,
                            'statusName': status_in_this_history,
                            'summary': summary,  
                            'labels': labels,    
                            'components': components,  
                            'assigneeUserName': issue_data['assignee'],
                            'assigneeDisplayName': issue_data['assignee'],
                            'reporterUserName': issue_data['reporter'],
                            'reporterDisplayName': issue_data['reporter'],
                            'allocationCode': allocation_code,
                            'projectKey': project_key,
                            'projectName': project_name,
                            'parentKey': parent_key,
                            'authorUserName': author_username,
                            'authorDisplayName': author_display,
                            'changes': changes,
                            'parent_issue': issue_data.get('parent_issue'),
                            'epic_issue': issue_data.get('epic_issue'),
                            'workingDaysFromCreation': working_days_from_creation_at_point,
                            'workingDaysInStatus': working_days_in_status_at_point,
                            'workingDaysFromMove': working_days_from_move_at_point
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