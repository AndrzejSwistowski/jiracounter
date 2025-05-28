"""
Jira Service module for JiraCounter application.

This module provides functionality to connect to the JIRA server and interact with the Jira API.
It uses the JIRA API token for authentication, with credentials retrieved from the config module.

All data is returned in ISO8601 format with timezone information.
"""

import logging
from typing import Optional, Dict, List, Any
from jira import JIRA
import config
from datetime import datetime, timedelta
from time_utils import (
    to_iso8601, parse_date, calculate_working_days_between, now, format_for_jql,
    find_status_change_date, find_first_status_change_date, calculate_days_since_date,
    calculate_working_minutes_since_date
)
from jira_field_manager import JiraFieldManager
from issue_data_extractor import IssueDataExtractor

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class JiraService:
    """Service class to interact with Jira API."""
    
    def __init__(self, jira_client=None):
        """Initialize the Jira service.
        
        Args:
            jira_client: Optional JIRA client for testing purposes
        """
        self.jira_client = jira_client
        self.connected = jira_client is not None
        self.field_manager = JiraFieldManager()
        self.data_extractor = IssueDataExtractor(self.field_manager)
        
    @property
    def field_ids(self):
        """Get the field_ids from the field manager."""
        return self.field_manager.field_ids
    
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
            self.field_manager.cache_field_ids(self.jira_client)
                
            return self.jira_client
            
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {str(e)}")
            self.connected = False
            raise ConnectionError(f"Could not connect to Jira: {str(e)}")
    
    # The _extract_issue_data method has been moved below the methods that use it
    
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

            return issue_data
        except ConnectionError as e:
            logger.error(f"Connection error retrieving issue {issue_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving issue {issue_key}: {str(e)}")
            raise

    def search_issues(self, jql_query: str, max_issues=None) -> List[Dict[str, Any]]:
        """Search for issues using JQL with automatic pagination.
        
        Args:
            jql_query: JQL query string
            max_issues: Maximum number of issues to process
            
        Returns:
            List of issues matching the query
        """
        jira = self.connect()
        all_issues = []
        
        try:
            # JIRA API typically limits each request to 100 items
            page_size = 100
            start_at = 0
            
            while True:
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
                
                # Check if we've reached the user-specified maximum
                if max_issues and len(all_issues) >= max_issues:
                    logger.info(f"Reached maximum issue limit of {max_issues}.")
                    break
                
            return all_issues
            
        except Exception as e:
            logger.error(f"Error searching issues with query {jql_query}: {str(e)}")
            raise
            
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
            # Expand both changelog and comments
            issue = jira.issue(issue_key, expand='changelog,comment,parent')
            
            # Get basic issue data
            issue_data = self._extract_issue_data(issue)
            
            changelog_entries = []
            status_change_history = []
            
            # Extract description content if it exists
            description_text = None
            if hasattr(issue.fields, 'description') and issue.fields.description:
                # Handle potentially large description text
                try:
                    description_text = issue.fields.description
                    # If description is very large, truncate it in logs to avoid log bloat
                    log_desc = description_text[:100] + "..." if len(description_text) > 100 else description_text
                    logger.debug(f"Found description for issue {issue_key}: {log_desc}")
                except Exception as e:
                    logger.warning(f"Error processing description for {issue_key}: {e}")
            
            # Extract comments if they exist
            comment_text = None
            if hasattr(issue.fields, 'comment') and hasattr(issue.fields.comment, 'comments'):
                try:
                    # Combine all comments into a single text field
                    all_comments = []
                    for comment in issue.fields.comment.comments:
                        if hasattr(comment, 'body') and comment.body:
                            comment_date = to_iso8601(comment.created) if hasattr(comment, 'created') else 'unknown'
                            author = comment.author.displayName if hasattr(comment, 'author') and hasattr(comment.author, 'displayName') else 'unknown'
                            comment_str = f"[{comment_date} by {author}] {comment.body}"
                            all_comments.append(comment_str)
                    
                    if all_comments:
                        comment_text = "\n\n".join(all_comments)
                        logger.debug(f"Found {len(all_comments)} comments for issue {issue_key}")
                except Exception as e:
                    logger.warning(f"Error processing comments for {issue_key}: {e}")
            
            # Create changes list for creation record
            creation_changes = []
            
            # Add description as a change item if it exists
            if description_text:
                creation_changes.append({
                    'field': 'description',
                    'fieldtype': 'jira',
                    'from': None,
                    'to': description_text
                })
                logger.debug(f"Added initial description to changes for issue {issue_key} (length: {len(description_text)})")
            
            # Create a history record for the issue creation
            creation_record = {
                'historyId': int(f"{issue.id}00000"),  # Use a synthetic ID for creation
                'historyDate': issue_data['created'],  # Store as ISO8601 format with timezone
                'factType': 1,  # 1 = create
                'issueId': issue.id,
                'issueKey': issue_key,
                'typeName': issue_data['type'],
                'statusName': 'Open',  # Assume issues start as Open
                'assigneeUserName': issue_data['assignee'],
                'assigneeDisplayName': issue_data['assignee'],
                'reporterUserName': issue_data['reporter'],
                'reporterDisplayName': issue_data['reporter'],
                'allocationCode': issue_data.get('allocation_code'),
                'projectKey': issue.fields.project.key,
                'projectName': issue.fields.project.name,
                'parentKey': issue_data.get('parent_issue', {}).get('key') if issue_data.get('parent_issue') else None,
                'authorUserName': issue_data['reporter'],
                'authorDisplayName': issue_data['reporter'],
                'changes': creation_changes,  # Include description as a change if it exists
                'summary': issue_data['summary'],
                'labels': issue_data['labels'],
                'components': issue_data['components'],
                'parent_issue': issue_data.get('parent_issue'),
                'parent_summary': issue_data.get('parent_issue', {}).get('summary') if issue_data.get('parent_issue') else None,        
                'epic_issue': issue_data.get('epic_issue'),
                'workingDaysFromCreation': 0,  # Just created, so 0 days
                'workingDaysInStatus': 0,      # Just created, so 0 days in status
                'working_days_from_move_at_point': None,    # No status change yet
                'todo_exit_date': None,
                "status_change_date": to_iso8601(issue_data['status_change_date']) if issue_data['status_change_date'] else None,
                "created": to_iso8601(issue_data['created']) if issue_data['created'] else None,
                "updated": to_iso8601(issue_data['updated']) if issue_data['updated'] else None,
                "description_text": description_text,  # Add description text field directly
                "comment_text": comment_text       # Add comments text field
            }
            
            changelog_entries.append(creation_record)
            
            # Extract and process changelog information
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
                histories = list(issue.changelog.histories)
                
                # Get status information
                status_name = issue_data['status']
                
                status_change_date = None
                working_days_in_status = None
                
                for history in histories:
                    for item in history.items:
                        if item.field == 'status' and item.toString == status_name:
                            status_change_date = parse_date(history.created)
                            break
                    if status_change_date:
                        break
                
                # If we found a status change date, calculate working days in status
                if status_change_date:
                    working_days_in_status = calculate_working_days_between(status_change_date, now())
                
                # Extract all changelog entries for further analysis
                for history in histories:
                    history_date = parse_date(history.created)
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
                    
                # Set initial todo_exit_date to None (will be populated with first status change)
                todo_exit_date = None
                initial_status_found = False
                
                # Sort status change history chronologically (oldest first)
                status_change_history.sort(key=lambda x: x['historyDate'])
                
                # First, determine what the initial status was
                initial_status = 'Open'  # Default assumption
                # If we have any status changes, check the first one to find the actual initial status
                for history_item in status_change_history:
                    for change in history_item['changes']:
                        if change['field'] == 'status':
                            initial_status = change['from']
                            initial_status_found = True
                            break
                    if initial_status_found:
                        break
                
                # Now find the first status change from this initial status
                for history_item in status_change_history:
                    for change in history_item['changes']:
                        if change['field'] == 'status' and change['from'] == initial_status:
                            todo_exit_date = history_item['historyDate']
                            logger.debug(f"Issue {issue_key} first status change from '{initial_status}' on {todo_exit_date}")
                            break
                    if todo_exit_date:
                        break
                
                # Process each changelog history
                for history in histories:
                    author = history.author.displayName if hasattr(history.author, 'displayName') else history.author.name
                    author_username = history.author.name if hasattr(history.author, 'name') else history.author.accountId
                    created = history.created
                    history_date = parse_date(created)
                    changes = []
                    
                    # Determine fact type (default to update)
                    fact_type = 3  # 3 = update
                    
                    for item in history.items:
                        changes.append({
                            'field': item.field,
                            'fieldtype': item.fieldtype if hasattr(item, 'fieldtype') else None,
                            'from': item.fromString,
                            'to': item.toString
                        })
                        
                        if item.field == 'status':
                            fact_type = 2  # 2 = transition
                    
                    # Calculate time-based metrics as of this history point
                    working_days_from_creation_at_point = calculate_working_days_between(issue_data['created'], history_date)
                    
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
                    
                    history_record = {
                        'historyId': int(history.id),
                        'historyDate': to_iso8601(history_date),
                        'factType': fact_type,
                        'issueId': issue.id,
                        'issueKey': issue_key,
                        'typeName': issue_data['type'],
                        'statusName': status_in_this_history,
                        'assigneeUserName': issue_data['assignee'],
                        'assigneeDisplayName': issue_data['assignee'],
                        'reporterUserName': issue_data['reporter'],
                        'reporterDisplayName': issue_data['reporter'],
                        'allocationCode': issue_data.get('allocation_code'),
                        'projectKey': issue.fields.project.key,
                        'projectName': issue.fields.project.name,
                        'parentKey': issue_data.get('parent_issue', {}).get('key') if issue_data.get('parent_issue') else None,
                        'authorUserName': author_username,
                        'authorDisplayName': author,
                        'changes': changes,
                        'summary': issue_data['summary'],
                        'labels': issue_data['labels'],
                        'components': issue_data['components'],
                        'parent_issue': issue_data.get('parent_issue'),
                        'parent_summary': issue_data.get('parent_issue', {}).get('summary') if issue_data.get('parent_issue') else None,        
                        'epic_issue': issue_data.get('epic_issue'),
                        'workingDaysFromCreation': working_days_from_creation_at_point,
                        'workingDaysInStatus': working_days_in_status_at_point,
                        'working_days_from_move_at_point': working_days_from_move_at_point,
                        'todo_exit_date': to_iso8601(todo_exit_date) if todo_exit_date else None,
                        "status_change_date": to_iso8601(issue_data['status_change_date']) if issue_data['status_change_date'] else None,
                        "created": to_iso8601(issue_data['created']) if issue_data['created'] else None,
                        "updated": to_iso8601(issue_data['updated']) if issue_data['updated'] else None,
                        "description_text": description_text,  # Add description text to all records
                        "comment_text": comment_text       # Add comments to all records
                    }
                    
                    changelog_entries.append(history_record)
            
            # Sort by history date
            changelog_entries.sort(key=lambda x: x['historyDate'])
            
            return changelog_entries
            
        except ConnectionError as e:
            logger.error(f"Connection error retrieving changelog for issue {issue_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving changelog for issue {issue_key}: {str(e)}")
            raise

    def get_issue_history(self, start_date=None, end_date=None, max_issues=None) -> List[Dict[str, Any]]:
        """Retrieve issue history records for issues updated within a date range.
        
        Args:
            start_date: The start date for the search (datetime or str)
            end_date: The end date for the search (datetime or str)
            max_issues: Maximum number of issues to process
            
        Returns:
            List of history records with standardized format
        """
        # Format dates for JQL consistently using time_utils function
        if start_date:
            start_str = format_for_jql(start_date)
        else:
            # Default to 7 days ago if no start date provided
            start_date = now() - timedelta(days=7)
            start_str = format_for_jql(start_date)
            
        if end_date:
            end_str = format_for_jql(end_date)
        else:
            end_date = now()
            end_str = format_for_jql(end_date)
            
        logger.info(f"Retrieving issues updated between {start_str} and {end_str}")
        
        # Build JQL query for issues updated in the date range
        jql = f'updated >= "{start_str}" AND updated <= "{end_str}" ORDER BY updated ASC'
        
        try:
            # Use search_issues method to get issues instead of direct connection
            issues = self.search_issues(jql, max_issues=max_issues)
            logger.info(f"Found {len(issues)} issues updated in the specified date range")
            
            # Process each issue to extract history records
            all_history_records = []
            
            for issue_data in issues:
                issue_key = issue_data['key']
                logger.debug(f"Processing changelog for issue {issue_key}")
                
                # Get detailed changelog using the enhanced get_issue_changelog method
                issue_history = self.get_issue_changelog(issue_key)
                
                # Don't filter history records by date - include all history
                # This ensures we don't miss any records that might have been 
                # updated during processing or that belong to a previous period
                # The consumer of this data can handle deduplication as needed
                all_history_records.extend(issue_history)
                
                # Log the number of history records found for this issue            logger.debug(f"Found {len(issue_history)} history records for issue {issue_key}")
            
            # Sort by history date
            all_history_records.sort(key=lambda x: x['created'])
            logger.info(f"Extracted {len(all_history_records)} history records")
            return all_history_records
            
        except Exception as e:
            logger.error(f"Error retrieving issue history: {str(e)}")
            raise
    
    def _extract_issue_data(self, issue) -> Dict[str, Any]:
        """Extract common issue data into a standardized dictionary.
        
        Args:
            issue: Jira issue object
            
        Returns:
            Dict containing the standardized issue details
        """        # Delegate to the IssueDataExtractor - it can handle both JIRA objects and dictionaries
        extracted_data = self.data_extractor.extract_issue_data(issue)
          # Return the extracted data (remove legacy code that duplicates extraction)
        return extracted_data# The _cache_field_ids method has been removed as this functionality
    # is now handled by the JiraFieldManager class
    
    # The get_field_id_by_name method has been removed as this functionality
    # is now handled by the JiraFieldManager class

    # The _extract_allocation_info method has been moved to the IssueDataExtractor class


# Usage example
if __name__ == "__main__":
    try:
        service = JiraService()
        jira = service.connect()

        issue = service.get_issue("PFBP-139")
        change_log = service.get_issue_changelog("PFBP-139")
        days_in_status = calculate_days_since_date(issue.get('status_change_date')) if issue.get('status_change_date') else "N/A"
        print(f"Issue: {issue['key']} - {issue['summary']} {issue['allocation_code']} ({issue['status']} - {days_in_status} days in status) - Created: {issue['created']} ({issue['minutes_since_creation']} minutes ago) - Reporter: {issue['reporter']} - Assignee: {issue['assignee']}")   
        print(f"Connected to Jira as {config.JIRA_USERNAME}")
        
        # Example: Get a sample project
        projects = jira.projects()
        if projects:
            print(f"Sample project: {projects[0].name} ({projects[0].key})")
    except Exception as e:
        print(f"Error: {str(e)}")