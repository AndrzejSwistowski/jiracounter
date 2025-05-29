"""
Issue History Extractor module for JiraCounter application.

This module handles extraction of issue history data from JIRA issues.
It follows the Single Responsibility Principle by focusing solely on history data extraction.
"""

import logging
from typing import Dict, Any, Optional, List
from time_utils import (
    to_iso8601, parse_date, calculate_working_days_between, now,
    find_status_change_date, calculate_working_minutes_since_date,
    calculate_working_minutes_between
)
from jira_field_manager import JiraFieldManager


class IssueHistoryExtractor:
    """
    Handles extraction of issue history data from JIRA issues.
    This class follows the Single Responsibility Principle by focusing solely on history data extraction.
    """
    
    def __init__(self, field_manager: JiraFieldManager, data_extractor):
        """
        Initialize the history extractor with a field manager and data extractor.
        
        Args:
            field_manager: JiraFieldManager instance for handling field operations
            data_extractor: IssueDataExtractor instance for extracting basic issue data
        """
        self.field_manager = field_manager
        self.data_extractor = data_extractor
        self.logger = logging.getLogger(__name__)
    
    def extract_issue_changelog(self, issue, issue_key: str) -> List[Dict[str, Any]]:
        """
        Extract comprehensive changelog data from a JIRA issue.
        
        This method serves as a template method that coordinates the history extraction process,
        delegating to specialized methods for each type of history data.
        
        Args:
            issue: JIRA issue object (expanded with changelog and comments)
            issue_key: The JIRA issue key for logging purposes
            
        Returns:
            List of changelog entries containing the history of changes with the following structure:
            
            [
                {
                    # Basic history information
                    'historyId': 12345,                    # History record ID (synthetic for creation)
                    'historyDate': '2023-01-01T10:00:00+00:00',  # Date of the change (ISO 8601)
                    'factType': 1,                         # 1=create, 2=transition, 3=update
                    
                    # Issue identification
                    'issueId': '12345',                    # JIRA issue ID
                    'issueKey': 'PROJECT-123',            # JIRA issue key
                    'typeName': 'Story',                   # Issue type
                    'statusName': 'In Progress',           # Status at this point in history
                    
                    # People information
                    'assigneeUserName': 'jdoe',           # Assignee username
                    'assigneeDisplayName': 'John Doe',    # Assignee display name
                    'reporterUserName': 'jsmith',         # Reporter username
                    'reporterDisplayName': 'Jane Smith',  # Reporter display name
                    'authorUserName': 'admin',            # Change author username
                    'authorDisplayName': 'Admin User',    # Change author display name
                    
                    # Project and hierarchy
                    'allocationCode': 'NEW',              # Work allocation code
                    'projectKey': 'PROJECT',              # Project key
                    'projectName': 'Project Name',        # Project name
                    'parentKey': 'PROJECT-122',           # Parent issue key (if any)
                    'parent_issue': {                     # Full parent issue info
                        'id': '12344',
                        'key': 'PROJECT-122',
                        'summary': 'Parent Issue'
                    },
                    'parent_summary': 'Parent Issue',     # Parent issue summary
                    'epic_issue': {                       # Epic information
                        'key': 'PROJECT-100',
                        'name': 'Feature Epic'
                    },
                    
                    # Change details
                    'changes': [                          # List of field changes in this history
                        {
                            'field': 'status',
                            'fieldtype': 'jira',
                            'from': 'Open',
                            'to': 'In Progress'
                        },
                        {
                            'field': 'assignee',
                            'fieldtype': 'jira',
                            'from': 'jsmith',
                            'to': 'jdoe'
                        }
                    ],
                    
                    # Issue content
                    'summary': 'Issue title',            # Issue summary
                    'labels': ['label1', 'label2'],      # Issue labels
                    'components': [                      # Issue components
                        {
                            'id': '1001',
                            'name': 'Frontend',
                            'description': 'UI components'
                        }
                    ],
                    'description_text': 'Issue description...',  # Full description text
                    'comment_text': '[2023-01-02T10:00:00+00:00 by John Doe] Comment text...',  # All comments                    # Time metrics (calculated at this history point)
                    'working_minutes_from_create': 7200, # Working minutes from creation to this history point
                    'working_minutes_in_status': 2880,   # Working minutes in current status at this point
                    'working_minutes_from_move_at_point': 4320, # Working minutes from first status change
                      # Categorized time metrics (working minutes spent in status categories)
                    'backlog_minutes': 1440,            # Working minutes spent in 'Backlog' status
                    'processing_minutes': 5760,         # Working minutes spent in processing statuses ('In progress', 'In review', 'testing')
                    'waiting_minutes': 2880,            # Working minutes spent in waiting statuses (all others except completed/backlog)
                    
                    # Status transition metrics (for workflow analysis)
                    'previous_status': 'In progress',   # Previous status before current one
                    'total_transitions': 3,             # Total number of status transitions
                    'backflow_count': 1,                # Number of backwards status transitions
                    'unique_statuses_visited': ['Open', 'In progress', 'In review'],  # All statuses this issue has been in
                    'status_transitions': [             # Detailed transition history
                        {
                            'from_status': 'Open',
                            'to_status': 'In progress', 
                            'transition_date': '2024-01-02T10:00:00+00:00',
                            'minutes_in_previous_status': 1440,
                            'is_forward_transition': True,
                            'is_backflow': False
                        }
                    ],
                    
                    'todo_exit_date': '2023-01-03T09:00:00+00:00',  # Date of first status change
                    
                    # Date fields (ISO 8601 format)
                    'status_change_date': '2023-01-10T09:00:00+00:00',  # Last status change date
                    'created': '2023-01-01T10:00:00+00:00',             # Issue creation date
                    'updated': '2023-01-15T14:30:00+00:00'              # Issue last update date
                }
            ]
            
            Note: The first entry will always be a creation record (factType=1) with synthetic historyId.
            Subsequent entries represent actual changes from the JIRA changelog.
        """
        try:
            # Get basic issue data using the data extractor
            issue_data = self.data_extractor.extract_issue_data(issue)
            
            changelog_entries = []
            
            # Extract description and comments
            description_text = self._extract_description(issue, issue_key)
            comment_text = self._extract_comments(issue, issue_key)
            
            # Create creation record
            creation_record = self._create_creation_record(
                issue, issue_key, issue_data, description_text, comment_text
            )
            changelog_entries.append(creation_record)
            
            # Extract and process changelog information
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
                # Process status change history for calculations
                status_change_history = self._extract_status_change_history(issue)
                
                # Calculate status-related metrics
                status_metrics = self._calculate_status_metrics(issue_data, status_change_history)
                
                # Find todo exit date (first status change)
                todo_exit_date = self._find_todo_exit_date(status_change_history)
                
                # Process each changelog history entry
                histories = list(issue.changelog.histories)
                for history in histories:
                    history_record = self._create_history_record(
                        history, issue, issue_key, issue_data, status_metrics,
                        status_change_history, todo_exit_date, description_text, comment_text
                    )
                    changelog_entries.append(history_record)
            
            # Sort by history date
            changelog_entries.sort(key=lambda x: x['historyDate'])
            
            return changelog_entries
            
        except Exception as e:
            self.logger.error(f"Error extracting changelog for issue {issue_key}: {str(e)}")
            raise
    
    def _extract_description(self, issue, issue_key: str) -> Optional[str]:
        """Extract description content from the issue."""
        description_text = None
        
        if hasattr(issue.fields, 'description') and issue.fields.description:
            try:
                description_text = issue.fields.description
                # If description is very large, truncate it in logs to avoid log bloat
                log_desc = description_text[:1000] + "..." if len(description_text) > 1000 else description_text
                self.logger.debug(f"Found description for issue {issue_key}: {log_desc}")
            except Exception as e:
                self.logger.warning(f"Error processing description for {issue_key}: {e}")
                
        return description_text
    
    def _extract_comments(self, issue, issue_key: str) -> Optional[str]:
        """Extract and combine all comments from the issue."""
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
                    self.logger.debug(f"Found {len(all_comments)} comments for issue {issue_key}")
            except Exception as e:
                self.logger.warning(f"Error processing comments for {issue_key}: {e}")
                
        return comment_text
    
    def _create_creation_record(self, issue, issue_key: str, issue_data: Dict[str, Any], 
                              description_text: Optional[str], comment_text: Optional[str]) -> Dict[str, Any]:
        """Create a synthetic creation record for the issue."""
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
            self.logger.debug(f"Added initial description to changes for issue {issue_key} (length: {len(description_text)})")
        
        return {
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
            'working_minutes_from_create': 0,  # Just created, so 0 minutes
            'working_minutes_in_status': 0,       # Just created, so 0 minutes in status
            'working_minutes_from_move_at_point': None,    # No status change yet            
            'backlog_minutes': 0,           # Just created, so 0 minutes in backlog
            'processing_minutes': 0,        # Just created, so 0 minutes in processing
            'waiting_minutes': 0,           # Just created, so 0 minutes waiting
            'previous_status': None,        # Just created, so no previous status
            'total_transitions': 0,         # Just created, so no transitions yet
            'backflow_count': 0,           # Just created, so no backflows yet
            'unique_statuses_visited': ['Open'],  # Just created, only initial status
            'status_transitions': [],       # Just created, no transitions yet
            'todo_exit_date': None,
            "status_change_date": to_iso8601(issue_data['status_change_date']) if issue_data['status_change_date'] else None,
            "created": to_iso8601(issue_data['created']) if issue_data['created'] else None,
            "updated": to_iso8601(issue_data['updated']) if issue_data['updated'] else None,
            "description_text": description_text,  # Add description text field directly
            "comment_text": comment_text       # Add comments text field
        }
    
    def _extract_status_change_history(self, issue) -> List[Dict[str, Any]]:
        """Extract all status changes from the changelog for analysis."""
        status_change_history = []
        
        if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
            histories = list(issue.changelog.histories)
            
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
        
        # Sort status change history chronologically (oldest first)
        status_change_history.sort(key=lambda x: x['historyDate'])
        return status_change_history
    
    def _calculate_categorized_time_metrics(self, status_change_history: List[Dict[str, Any]], 
                                           creation_date: Any, update_date: Any) -> Dict[str, Any]:
        """
        Calculate time spent in different status categories.
        
        Categories:
        - Backlog: Time in 'Backlog' status
        - Processing: Time in 'In progress', 'In review', 'testing' statuses
        - Waiting: Time in all other statuses (except 'Completed' and 'Backlog')
        
        Args:
            status_change_history: List of status changes chronologically sorted
            creation_date: Issue creation date
            update_date: Issue last update date
            
        Returns:
            Dictionary with working minutes for each category:
            {
                'backlog_minutes': int,
                'processing_minutes': int, 
                'waiting_minutes': int
            }
        """
        # Define status categories
        processing_statuses = {'In progress', 'In review', 'testing'}
        backlog_statuses = {'Backlog'}
        completed_statuses = {'Completed', 'Done', 'Closed', 'Resolved'}
        
        # Initialize counters
        backlog_minutes = 0
        processing_minutes = 0
        waiting_minutes = 0
        
        # Track current status and when it started
        current_status = None
        status_start_date = creation_date
        
        # If there are no status changes, we need to determine the initial status
        # and calculate time based on that
        if not status_change_history:
            # Default initial status is usually 'Open' or similar - categorize as waiting
            total_minutes = calculate_working_minutes_between(creation_date, update_date)
            waiting_minutes = total_minutes
            return {
                'backlog_minutes': backlog_minutes,
                'processing_minutes': processing_minutes,
                'waiting_minutes': waiting_minutes
            }
        
        # Find the initial status from the first status change
        initial_status = None
        for history in status_change_history:
            for change in history['changes']:
                if change['field'] == 'status':
                    initial_status = change['from']
                    break
            if initial_status:
                break
        
        # If we couldn't find initial status, assume 'Open'
        if not initial_status:
            initial_status = 'Open'
        
        current_status = initial_status
        
        # Process each status change
        for history in status_change_history:
            for change in history['changes']:
                if change['field'] == 'status':
                    # Calculate time spent in previous status
                    time_in_status = calculate_working_minutes_between(status_start_date, history['historyDate'])
                      # Categorize the time based on the status we're leaving
                    if current_status in backlog_statuses:
                        backlog_minutes += time_in_status
                    elif current_status in processing_statuses:
                        processing_minutes += time_in_status
                    elif current_status not in completed_statuses:
                        # Not in backlog, processing, or completed = waiting
                        waiting_minutes += time_in_status
                    # If in completed status, we don't count the time
                    
                    # Update for next iteration
                    current_status = change['to']
                    status_start_date = history['historyDate']
                    break
        
        # Calculate time spent in final status (from last change to update date)
        if current_status not in completed_statuses:
            time_in_final_status = calculate_working_minutes_between(status_start_date, update_date)
            
            if current_status in backlog_statuses:
                backlog_minutes += time_in_final_status
            elif current_status in processing_statuses:
                processing_minutes += time_in_final_status
            else:
                waiting_minutes += time_in_final_status
        
        return {
            'backlog_minutes': backlog_minutes,
            'processing_minutes': processing_minutes,
            'waiting_minutes': waiting_minutes
        }

    def _calculate_status_transition_metrics(self, status_change_history: List[Dict[str, Any]], 
                                           creation_date: Any, update_date: Any) -> Dict[str, Any]:
        """
        Calculate detailed status transition metrics for advanced reporting.
        
        This method tracks each status transition with timing information,
        enabling analysis of workflow patterns, bottlenecks, and backflows.
        
        Args:
            status_change_history: List of status changes chronologically sorted
            creation_date: Issue creation date
            update_date: Issue last update date
            
        Returns:
            Dictionary with transition metrics:
            {
                'status_transitions': [
                    {
                        'from_status': 'Open',
                        'to_status': 'In progress', 
                        'transition_date': '2024-01-02T10:00:00+00:00',
                        'minutes_in_previous_status': 1440,
                        'is_forward_transition': True,
                        'is_backflow': False
                    }
                ],
                'current_status': 'In review',
                'previous_status': 'In progress',
                'total_transitions': 3,
                'backflow_count': 0,
                'unique_statuses_visited': ['Open', 'In progress', 'In review']
            }
        """
        # Initialize result structure
        transitions = []
        unique_statuses = set()
        backflow_count = 0
        
        # Define typical workflow order for backflow detection
        workflow_order = {
            'Open': 1, 'Backlog': 2, 'Selected': 3, 'In progress': 4, 
            'In review': 5, 'testing': 6, 'Done': 7, 'Completed': 8, 'Closed': 9
        }
        
        # Track current status and timing
        current_status = None
        previous_status = None
        status_start_date = creation_date
        
        # If no status changes, return minimal data
        if not status_change_history:
            return {
                'status_transitions': [],
                'current_status': 'Open',  # Default initial status
                'previous_status': None,
                'total_transitions': 0,
                'backflow_count': 0,
                'unique_statuses_visited': ['Open']
            }
          # Find initial status from first change
        initial_status = 'Open'  # Default
        for history in status_change_history:
            for change in history['changes']:
                if change['field'] == 'status':
                    initial_status = change['from']
                    break
            if initial_status:  # Break when we find any initial status
                break
        
        current_status = initial_status
        unique_statuses.add(initial_status)
        
        # Process each status change
        for history in status_change_history:
            for change in history['changes']:
                if change['field'] == 'status':
                    # Calculate time spent in previous status
                    minutes_in_previous = calculate_working_minutes_between(
                        status_start_date, history['historyDate']
                    )
                    
                    # Determine if this is a backflow (moving to "earlier" status)
                    from_order = workflow_order.get(current_status, 0)
                    to_order = workflow_order.get(change['to'], 0)
                    is_backflow = from_order > to_order and from_order > 0 and to_order > 0
                    is_forward = from_order < to_order and from_order > 0 and to_order > 0
                    
                    if is_backflow:
                        backflow_count += 1
                    
                    # Record transition
                    transition = {
                        'from_status': current_status,
                        'to_status': change['to'],
                        'transition_date': to_iso8601(history['historyDate']),
                        'minutes_in_previous_status': minutes_in_previous,
                        'is_forward_transition': is_forward,
                        'is_backflow': is_backflow
                    }
                    transitions.append(transition)
                    
                    # Update tracking variables
                    previous_status = current_status
                    current_status = change['to']
                    unique_statuses.add(current_status)
                    status_start_date = history['historyDate']
                    break
        
        # Calculate time in current status (if not completed)
        completed_statuses = {'Completed', 'Done', 'Closed', 'Resolved'}
        current_status_minutes = 0
        if current_status not in completed_statuses:
            current_status_minutes = calculate_working_minutes_between(status_start_date, update_date)
        
        return {
            'status_transitions': transitions,
            'current_status': current_status,
            'previous_status': previous_status,
            'total_transitions': len(transitions),
            'backflow_count': backflow_count,
            'unique_statuses_visited': list(unique_statuses),
            'current_status_minutes': current_status_minutes
        }

    def _calculate_status_metrics(self, issue_data: Dict[str, Any], 
                                status_change_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate status-related metrics for the issue."""
        status_name = issue_data['status']
        status_change_date = None
        working_minutes_in_status = None
        
        # Find the most recent status change to the current status
        for history in status_change_history:
            for change in history['changes']:
                if change['field'] == 'status' and change['to'] == status_name:
                    status_change_date = history['historyDate']
                    break
            if status_change_date:
                break
        
        # If we found a status change date, calculate working minutes in status
        if status_change_date:
            working_minutes_in_status = calculate_working_minutes_between(status_change_date, now())        # Calculate categorized time metrics
        creation_date = issue_data.get('created')
        update_date = issue_data.get('updated')
        categorized_metrics = self._calculate_categorized_time_metrics(status_change_history, creation_date, update_date)
        
        # Calculate status transition metrics
        transition_metrics = self._calculate_status_transition_metrics(status_change_history, creation_date, update_date)
        
        return {
            'status_name': status_name,
            'status_change_date': status_change_date,
            'working_minutes_in_status': working_minutes_in_status,
            'backlog_minutes': categorized_metrics['backlog_minutes'],
            'processing_minutes': categorized_metrics['processing_minutes'],
            'waiting_minutes': categorized_metrics['waiting_minutes'],
            'previous_status': transition_metrics['previous_status'],
            'total_transitions': transition_metrics['total_transitions'],
            'backflow_count': transition_metrics['backflow_count'],
            'unique_statuses_visited': transition_metrics['unique_statuses_visited'],
            'status_transitions': transition_metrics['status_transitions']
        }
    
    def _find_todo_exit_date(self, status_change_history: List[Dict[str, Any]]) -> Optional[Any]:
        """Find the date when the issue first changed status from its initial status."""
        todo_exit_date = None
        initial_status_found = False
        
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
                    self.logger.debug(f"First status change from '{initial_status}' on {todo_exit_date}")
                    break
            if todo_exit_date:
                break
        
        return todo_exit_date
    
    def _create_history_record(self, history, issue, issue_key: str, issue_data: Dict[str, Any],
                             status_metrics: Dict[str, Any], status_change_history: List[Dict[str, Any]],
                             todo_exit_date: Optional[Any], description_text: Optional[str],
                             comment_text: Optional[str]) -> Dict[str, Any]:
        """Create a history record from a changelog history entry."""
        # Extract author information
        author = history.author.displayName if hasattr(history.author, 'displayName') else history.author.name
        author_username = history.author.name if hasattr(history.author, 'name') else history.author.accountId
        
        # Parse history date
        created = history.created
        history_date = parse_date(created)
        
        # Extract changes
        changes = []
        fact_type = 3  # 3 = update (default)
        
        for item in history.items:
            changes.append({
                'field': item.field,
                'fieldtype': item.fieldtype if hasattr(item, 'fieldtype') else None,
                'from': item.fromString,
                'to': item.toString
            })
            
            if item.field == 'status':
                fact_type = 2  # 2 = transition        # Calculate time-based metrics as of this history point
        working_minutes_from_creation_at_point = calculate_working_minutes_between(
            parse_date(issue_data['created']), history_date
        )
          # For each history point, determine how long it had been in the current status
        status_in_this_history = status_metrics['status_name']  # Default to current status
        working_minutes_in_status_at_point = status_metrics['working_minutes_in_status']
        
        # Check if this history changes the status
        for change in changes:
            if change['field'] == 'status':
                # If this is a status change, find how long it was in the previous status
                previous_status_change = find_status_change_date(
                    status_change_history, change['from'], None
                )
                if previous_status_change:
                    working_minutes_in_status_at_point = calculate_working_minutes_between(
                        previous_status_change, history_date
                    )
                status_in_this_history = change['to']
                break
          # Calculate working minutes from first status change at this history point
        working_minutes_from_move_at_point = None
        if todo_exit_date and history_date >= todo_exit_date:
            working_minutes_from_move_at_point = calculate_working_minutes_between(
                todo_exit_date, history_date
            )
        
        return {
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
            'working_minutes_from_create': working_minutes_from_creation_at_point,
            'working_minutes_in_status': working_minutes_in_status_at_point,
            'working_minutes_from_move_at_point': working_minutes_from_move_at_point,            'backlog_minutes': status_metrics['backlog_minutes'],
            'processing_minutes': status_metrics['processing_minutes'],
            'waiting_minutes': status_metrics['waiting_minutes'],
            'previous_status': status_metrics['previous_status'],
            'total_transitions': status_metrics['total_transitions'],
            'backflow_count': status_metrics['backflow_count'],
            'unique_statuses_visited': status_metrics['unique_statuses_visited'],
            'status_transitions': status_metrics['status_transitions'],
            'todo_exit_date': to_iso8601(todo_exit_date) if todo_exit_date else None,
            "status_change_date": to_iso8601(issue_data['status_change_date']) if issue_data['status_change_date'] else None,
            "created": to_iso8601(issue_data['created']) if issue_data['created'] else None,
            "updated": to_iso8601(issue_data['updated']) if issue_data['updated'] else None,
            "description_text": description_text,  # Add description text to all records
            "comment_text": comment_text       # Add comments to all records
        }
    
    def safe_get_field(self, obj, field_name, default=None):
        """Helper function to safely get a field from an object regardless of its type.
        Delegates to JiraFieldManager's safe_get_field method to avoid code duplication.
        
        Args:
            obj: The object to extract a field from
            field_name: The name of the field to extract
            default: Default value to return if the field doesn't exist
            
        Returns:
            The value of the field or the default value
        """
        return self.field_manager.safe_get_field(obj, field_name, default)
