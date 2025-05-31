"""
Issue History Extractor module for JiraCounter application.

This module handles extraction of issue history data from JIRA issues.
It follows the Single Responsibility Principle by focusing solely on history data extraction.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from time_utils import (
    to_iso8601, parse_date, calculate_working_days_between, now,
    find_status_change_date, calculate_working_minutes_since_date,
    calculate_working_minutes_between, format_working_minutes_to_text
)
from jira_field_manager import JiraFieldManager


class IssueHistoryExtractor:
    """
    Handles extraction of issue history data from JIRA issues.
    This class follows the Single Responsibility Principle by focusing solely on history data extraction.    """
    
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

    def extract_issue_changelog(self, issue, issue_key: str) -> Dict[str, Any]:
        """
        Extract comprehensive issue data with complete history and metrics.
        
        This method creates a single comprehensive record per issue containing current state
        and all historical data, eliminating the overhead of duplicating issue data.
        
        Args:
            issue: JIRA issue object (expanded with changelog and comments)
            issue_key: The JIRA issue key for logging purposes
            
        Returns:
            Single comprehensive issue record with the following structure:
            
            {
                # Current issue data (latest state)
                'issue_data': {
                    'issueId': '12345',
                    'issueKey': 'PROJECT-123',
                    'type': 'Story',
                    'status': 'In Progress',
                    'assignee': {'username': 'jdoe', 'display_name': 'John Doe'},
                    'reporter': {'username': 'jsmith', 'display_name': 'Jane Smith'},
                    'allocation_code': 'NEW',
                    'project_key': 'PROJECT',
                    'project_name': 'Project Name',
                    'parent_issue': {'key': 'PROJECT-122', 'summary': 'Parent Issue'},
                    'epic_issue': {'key': 'PROJECT-100', 'name': 'Feature Epic'},
                    'summary': 'Issue title',
                    'labels': ['label1', 'label2'],
                    'components': [{'id': '1001', 'name': 'Frontend'}],
                    'created': datetime_object,
                    'updated': datetime_object,
                    'status_change_date': datetime_object
                },
                
                # Content fields
                'issue_description': 'Issue description...',  # Full description text
                'issue_comments': [  # Array of comment objects
                    {
                        'created_at': '2023-01-02T10:00:00+00:00',
                        'body': 'Comment text...',
                        'author': 'John Doe'
                    }
                ],
                
                # Current time metrics (as of latest update)
                'metrics': {
                    'working_minutes_from_create': 7200,     # Total working minutes since creation
                    'working_minutes_in_current_status': 2880, # Working minutes in current status
                    'working_minutes_from_first_move': 4320,  # Working minutes since first status change
                    
                    # Categorized time metrics (working minutes spent in status categories)
                    'backlog_minutes': 1440,                 # Working minutes spent in 'Backlog' status
                    'processing_minutes': 5760,              # Working minutes spent in processing statuses
                    'waiting_minutes': 2880,                 # Working minutes spent in waiting statuses
                    
                    # Status transition summary
                    'previous_status': 'In progress',        # Previous status before current one
                    'total_transitions': 3,                  # Total number of status transitions
                    'backflow_count': 1,                     # Number of backwards status transitions
                    'unique_statuses_visited': ['Open', 'In progress', 'In review'], # All statuses visited
                    'todo_exit_date': '2023-01-03T09:00:00+00:00'  # Date of first status change
                },
                
                # Complete status transition history
                'status_transitions': [
                    {
                        'from_status': 'Open',
                        'to_status': 'In progress', 
                        'transition_date': '2024-01-02T10:00:00+00:00',
                        'minutes_in_previous_status': 1440,
                        'is_forward_transition': True,
                        'is_backflow': False,
                        'author': 'John Doe'
                    }
                ],
                
                # Non-status changes history (all other field changes)
                'field_changes': [
                    {
                        'change_date': '2023-01-04T14:30:00+00:00',
                        'author': 'Jane Smith',
                        'changes': [
                            {
                                'field': 'assignee',
                                'fieldtype': 'jira',
                                'from': 'John Doe',
                                'to': 'Jane Smith'
                            }
                        ]
                    }
                ]            }
        """
        try:
            # Get basic issue data using the data extractor
            issue_data = self.data_extractor.extract_issue_data(issue)
            
            # Extract description and comments
            issue_description = self._extract_description(issue, issue_key)
            issue_comments = self._extract_comments(issue, issue_key)
            
            # Extract and process changelog information
            status_transitions = []
            field_changes = []
            
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
                # Process status change history for calculations
                status_change_history = self._extract_status_change_history(issue)
                
                # Calculate status-related metrics
                status_metrics = self._calculate_status_metrics(issue_data, status_change_history)
                
                # Extract status transitions with detailed information
                status_transitions = self._extract_detailed_status_transitions(issue)
                
                # Extract non-status field changes
                field_changes = self._extract_field_changes(issue)
            else:
                # No changelog available, create minimal metrics
                status_metrics = {
                    'working_minutes_from_create': 0,
                    'working_minutes_in_current_status': 0,
                    'working_minutes_from_first_move': 0,
                    'backlog_minutes': 0,
                    'processing_minutes': 0,
                    'waiting_minutes': 0,
                    'previous_status': None,
                    'total_transitions': 0,
                    'backflow_count': 0,
                    'unique_statuses_visited': [issue_data.get('status', 'Unknown')],
                    'todo_exit_date': None
                }
            
            # Build comprehensive issue record
            comprehensive_record = {
                # Current issue data (latest state)
                'issue_data': issue_data,
                
                # Content fields
                'issue_description': issue_description,
                'issue_comments': issue_comments,
                
                # Current time metrics (as of latest update)
                'metrics': status_metrics,
                
                # Complete status transition history
                'status_transitions': status_transitions,
                
                # Non-status changes history (all other field changes)
                'field_changes': field_changes
            }
            
            return comprehensive_record
            
        except Exception as e:
            self.logger.error(f"Error extracting comprehensive issue data for {issue_key}: {str(e)}")
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

    def _extract_comments(self, issue, issue_key: str) -> Optional[list]:
        """Extract all comments from the issue as an array of comment objects."""
        comments_array = None
        
        if hasattr(issue.fields, 'comment') and hasattr(issue.fields.comment, 'comments'):
            try:
                # Extract comments as an array of objects
                comments_array = []
                for comment in issue.fields.comment.comments:
                    if hasattr(comment, 'body') and comment.body:
                        created_at = to_iso8601(comment.created) if hasattr(comment, 'created') else None
                        author = comment.author.displayName if hasattr(comment, 'author') and hasattr(comment.author, 'displayName') else None
                        
                        comment_obj = {
                            'created_at': created_at,
                            'body': comment.body,
                            'author': author
                        }
                        comments_array.append(comment_obj)
                        
                if comments_array:
                    self.logger.debug(f"Found {len(comments_array)} comments for issue {issue_key}")
                else:
                    comments_array = None  # Return None if no comments found
            except Exception as e:
                self.logger.warning(f"Error processing comments for {issue_key}: {e}")                
        return comments_array
    
    def _create_creation_record(self, issue, issue_key: str, issue_data: Dict[str, Any], 
                              issue_description: Optional[str], issue_comments: Optional[list]) -> Dict[str, Any]:
        """Create a synthetic creation record for the issue."""
        # Create changes list for creation record
        creation_changes = []
          # Add description as a change item if it exists
        if issue_description:
            creation_changes.append({
                'field': 'description',
                'fieldtype': 'jira',
                'from': None,
                'to': issue_description
            })
            self.logger.debug(f"Added initial description to changes for issue {issue_key} (length: {len(issue_description)})")
        
        # Create a copy of issue_data for the creation record and set initial status
        creation_issue_data = issue_data.copy()
        creation_issue_data['status'] = 'Backlog'  # Assume issues start as Backlog
        
        return {
            'historyId': int(f"{issue.id}00000"),  # Use a synthetic ID for creation
            'historyDate': to_iso8601(issue_data['created']),  # Store as ISO8601 format with timezone
            'factType': 1,  # 1 = create
            
            # Include complete issue data
            'issue_data': creation_issue_data,
              # Author information (for creation record, author is the reporter)
            'authorUserName': issue_data['reporter']['name'] if issue_data['reporter'] else None,
            'authorDisplayName': issue_data['reporter']['display_name'] if issue_data['reporter'] else None,
            
            # Change details
            'changes': creation_changes,  # Include description as a change if it exists
              # Content fields
            'issue_description': issue_description,  # Add description text field directly
            'issue_comments': issue_comments,       # Add comments text field
            
            # Time metrics (all zero for creation record)
            'working_minutes_from_create': 0,  # Just created, so 0 minutes
            'working_minutes_in_status': 0,       # Just created, so 0 minutes in status
            'working_minutes_from_move_at_point': None,    # No status change yet
            
            # Categorized time metrics (all zero for creation record)
            'backlog_minutes': 0,           # Just created, so 0 minutes in backlog
            'processing_minutes': 0,        # Just created, so 0 minutes in processing
            'waiting_minutes': 0,           # Just created, so 0 minutes waiting
            
            # Status transition metrics (initial values for creation record)
            'previous_status': None,        # Just created, so no previous status
            'total_transitions': 0,         # Just created, so no transitions yet
            'backflow_count': 0,           # Just created, so no backflows yet
            'unique_statuses_visited': ['Backlog'],  # Just created, only initial status
            'status_transitions': [],       # Just created, no transitions yet
            
            # Date fields
            'todo_exit_date': None  # No todo exit date for creation record
        }
      
    def _extract_status_change_history(self, issue) -> List[Dict[str, Any]]:
        """Extract all status changes from the changelog for analysis."""
        status_change_history = []
        
        if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
            histories = list(issue.changelog.histories)
            
            for history in histories:
                history_date = parse_date(history.created)
                status_changes = []
                
                # Only include status field changes
                for item in history.items:
                    if item.field == 'status':
                        status_changes.append({
                            'field': item.field,
                            'from': item.fromString,
                            'to': item.toString
                        })
                
                # Only add history entry if it contains status changes
                if status_changes:
                    status_change_history.append({
                        'historyDate': history_date,                    
                        'changes': status_changes
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
        """        # Define status categories (case-insensitive)
        processing_statuses = {'in progress', 'in review', 'testing'}
        backlog_statuses = {'backlog'}
        completed_statuses = {'completed', 'done', 'closed', 'resolved'}
        
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
            # Default initial status is usually 'Backlog' or similar - categorize as backlog
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
        
        # If we couldn't find initial status, assume 'Backlog'
        if not initial_status:
            initial_status = 'Backlog'
        
        current_status = initial_status
        
        # Process each status change
        for history in status_change_history:
            for change in history['changes']:
                if change['field'] == 'status':
                    # Calculate time spent in previous status
                    time_in_status = calculate_working_minutes_between(status_start_date, history['historyDate'])                    # Categorize the time based on the status we're leaving
                    if self._is_in_category(current_status, backlog_statuses):
                        backlog_minutes += time_in_status
                    elif self._is_in_category(current_status, processing_statuses):
                        processing_minutes += time_in_status
                    elif not self._is_in_category(current_status, completed_statuses):
                        # Not in backlog, processing, or completed = waiting
                        waiting_minutes += time_in_status
                    # If in completed status, we don't count the time
                    
                    # Update for next iteration
                    current_status = change['to']
                    status_start_date = history['historyDate']
                    break        # Calculate time spent in final status (from last change to update date)
        if not self._is_in_category(current_status, completed_statuses):
            time_in_final_status = calculate_working_minutes_between(status_start_date, update_date)
            
            if self._is_in_category(current_status, backlog_statuses):
                backlog_minutes += time_in_final_status
            elif self._is_in_category(current_status, processing_statuses):
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
        backflow_count = 0        # Define typical workflow order for backflow detection (case-insensitive)
        workflow_order_base = {
            'backlog': 1,
            'draft': 2,
            'open': 3,
            'hold': 4,
            'planned': 5,
            'selected for development': 6,
            'do poprawy': 7,
            'in progress': 8,
            'ready for review': 9,
            'in review': 10,
            'ready for testing': 11,
            'testy wewnętrzne': 12,
            'testing': 13,
            'do akceptacji klienta': 14,
            'awaiting production release': 15,
            'customer notification': 16,
            'closed': 17,
            'canceled': 18,
            'completed': 19,
            'done': 20
        }
        
        def get_workflow_order(status_name):
            """Get workflow order for a status name in a case-insensitive way."""
            if not status_name:
                return 0
            return workflow_order_base.get(status_name.lower().strip(), 0)
        
        # Track current status and timing
        current_status = None
        previous_status = None
        status_start_date = creation_date
          # If no status changes, return minimal data
        if not status_change_history:
            return {
                'status_transitions': [],
                'current_status': 'Backlog',  # Default initial status
                'previous_status': None,
                'total_transitions': 0,
                'backflow_count': 0,
                'unique_statuses_visited': ['Backlog']
            }
          # Find initial status from first change
        initial_status = 'Backlog'  # Default
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
                    from_order = get_workflow_order(current_status)
                    to_order = get_workflow_order(change['to'])
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
                    break        # Calculate time in current status (if not completed)
        completed_statuses_check = {'completed', 'done', 'closed', 'resolved'}
        current_status_minutes = 0
        if not self._is_in_category(current_status, completed_statuses_check):
            current_status_minutes = calculate_working_minutes_between(status_start_date, update_date)
        
        return {
            'status_transitions': transitions,
            'current_status': current_status,
            'previous_status': previous_status,
            'total_transitions': len(transitions),
            'backflow_count': backflow_count,
            'unique_statuses_visited': list(unique_statuses),            'current_status_minutes': current_status_minutes
        }

    def _calculate_status_metrics(self, issue_data: Dict[str, Any], 
                                status_change_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate status-related metrics for the issue."""
        creation_date = issue_data.get('created')
        update_date = issue_data.get('updated')
        
        # Calculate total working minutes from creation
        working_minutes_from_create = 0
        if creation_date and update_date:
            working_minutes_from_create = calculate_working_minutes_between(creation_date, update_date)
        
        # Find current status change date and calculate minutes in current status
        status_name = issue_data['status']
        status_change_date = None
        working_minutes_in_current_status = 0
        
        # Find the most recent status change to the current status
        for history in reversed(status_change_history):
            for change in history['changes']:
                if change['field'] == 'status' and change['to'] == status_name:
                    status_change_date = history['historyDate']
                    break
            if status_change_date:
                break
        
        # Calculate working minutes in current status
        if status_change_date:
            working_minutes_in_current_status = calculate_working_minutes_between(status_change_date, update_date)
        else:
            # If no status change found, time in status equals total time from creation
            working_minutes_in_current_status = working_minutes_from_create
        
        # Calculate working minutes from first move (todo exit date)
        todo_exit_date = self._find_todo_exit_date(status_change_history)
        working_minutes_from_first_move = 0
        if todo_exit_date and update_date:
            working_minutes_from_first_move = calculate_working_minutes_between(todo_exit_date, update_date)
        
        # Calculate categorized time metrics
        categorized_metrics = self._calculate_categorized_time_metrics(status_change_history, creation_date, update_date)
        
        # Calculate status transition metrics
        transition_metrics = self._calculate_status_transition_metrics(status_change_history, creation_date, update_date)
        
        return {
            'working_minutes_from_create': working_minutes_from_create,
            'working_minutes_in_current_status': working_minutes_in_current_status,
            'working_minutes_from_first_move': working_minutes_from_first_move,
            'backlog_minutes': categorized_metrics['backlog_minutes'],
            'processing_minutes': categorized_metrics['processing_minutes'],
            'waiting_minutes': categorized_metrics['waiting_minutes'],
            'previous_status': transition_metrics['previous_status'],
            'total_transitions': transition_metrics['total_transitions'],
            'backflow_count': transition_metrics['backflow_count'],
            'unique_statuses_visited': transition_metrics['unique_statuses_visited'],
            'todo_exit_date': to_iso8601(todo_exit_date) if todo_exit_date else None
        }
    
    def _find_todo_exit_date(self, status_change_history: List[Dict[str, Any]]) -> Optional[Any]:
        """Find the date when the issue first changed status from its initial status."""
        todo_exit_date = None
        initial_status_found = False
        
        # First, determine what the initial status was
        initial_status = 'Backlog'  # Default assumption
        
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
                             todo_exit_date: Optional[Any], issue_description: Optional[str],
                             issue_comments: Optional[list]) -> Dict[str, Any]:
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
                fact_type = 2  # 2 = transition

        # Calculate time-based metrics as of this history point
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
        
        # Create a copy of issue_data and update the status for this history point
        history_issue_data = issue_data.copy()
        history_issue_data['status'] = status_in_this_history
        
        return {
            'historyId': int(history.id),
            'historyDate': to_iso8601(history_date),
            'factType': fact_type,
            
            # Include complete issue data
            'issue_data': history_issue_data,
            
            # Author information
            'authorUserName': author_username,
            'authorDisplayName': author,
            
            # Change details
            'changes': changes,
              # Content fields
            'issue_description': issue_description,  # Add description text to all records
            'issue_comments': issue_comments,       # Add comments to all records
            
            # Time metrics
            'working_minutes_from_create': working_minutes_from_creation_at_point,
            'working_minutes_in_status': working_minutes_in_status_at_point,
            'working_minutes_from_move_at_point': working_minutes_from_move_at_point,
            
            # Categorized time metrics
            'backlog_minutes': status_metrics['backlog_minutes'],
            'processing_minutes': status_metrics['processing_minutes'],
            'waiting_minutes': status_metrics['waiting_minutes'],
            
            # Status transition metrics
            'previous_status': status_metrics['previous_status'],
            'total_transitions': status_metrics['total_transitions'],
            'backflow_count': status_metrics['backflow_count'],
            'unique_statuses_visited': status_metrics['unique_statuses_visited'],
            'status_transitions': status_metrics['status_transitions'],
            
            # Date fields
            'todo_exit_date': to_iso8601(todo_exit_date) if todo_exit_date else None
        }
    
    def _extract_detailed_status_transitions(self, issue) -> List[Dict[str, Any]]:
        """
        Extract detailed status transitions with author information and timing.
        
        Args:
            issue: JIRA issue object with changelog
            
        Returns:
            List of status transition records with detailed information
        """
        transitions = []
        
        if not (hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories')):
            return transitions
        
        # Get status change history for timing calculations
        status_change_history = self._extract_status_change_history(issue)
        
        # Track timing for each transition
        previous_status_start = issue.fields.created if hasattr(issue.fields, 'created') else None
        
        for i, history in enumerate(status_change_history):
            for change in history['changes']:
                if change['field'] == 'status':
                    # Calculate time spent in previous status
                    minutes_in_previous = 0
                    if previous_status_start:
                        minutes_in_previous = calculate_working_minutes_between(
                            previous_status_start, history['historyDate']
                        )
                    
                    # Find the original history record for author information
                    author_name = None
                    author_display = None
                    for orig_history in issue.changelog.histories:
                        if parse_date(orig_history.created) == history['historyDate']:
                            if hasattr(orig_history, 'author'):
                                author_name = orig_history.author.name if hasattr(orig_history.author, 'name') else None
                                author_display = orig_history.author.displayName if hasattr(orig_history.author, 'displayName') else None
                            break
                    
                    # Determine if this is a forward or backward transition
                    is_forward, is_backflow = self._analyze_transition_direction(
                        change['from'], change['to']
                    )
                      # Calculate days and time period string for minutes_in_previous_status
                    # Using 8-hour working days (60 * 8 = 480 minutes per day)
                    days_in_previous = int(minutes_in_previous / 480) if minutes_in_previous else 0
                    period_text = format_working_minutes_to_text(minutes_in_previous) if minutes_in_previous else None
                    
                    transition_record = {
                        'from_status': change['from'],
                        'to_status': change['to'],
                        'transition_date': to_iso8601(history['historyDate']),
                        'minutes_in_previous_status': minutes_in_previous,
                        'days_in_previous_status': days_in_previous,
                        'period_in_previous_status': period_text,
                        'is_forward_transition': is_forward,
                        'is_backflow': is_backflow,
                        'author': author_display or author_name
                    }
                    
                    transitions.append(transition_record)
                    
                    # Update for next iteration
                    previous_status_start = history['historyDate']
                    break
        
        return transitions
    
    def _extract_field_changes(self, issue) -> List[Dict[str, Any]]:
        """
        Extract all non-status field changes from the changelog.
        
        Args:
            issue: JIRA issue object with changelog
            
        Returns:
            List of field change records grouped by change date
        """
        field_changes = []
        
        if not (hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories')):
            return field_changes
        
        for history in issue.changelog.histories:
            # Collect all non-status changes for this history entry
            non_status_changes = []
            
            for item in history.items:
                if item.field != 'status':  # Exclude status changes
                    change_record = {
                        'field': item.field,
                        'fieldtype': getattr(item, 'fieldtype', 'jira'),
                        'from': item.fromString,
                        'to': item.toString
                    }
                    non_status_changes.append(change_record)
            
            # Only add if there are non-status changes
            if non_status_changes:
                # Get author information
                author_name = None
                author_display = None
                if hasattr(history, 'author'):
                    author_name = history.author.name if hasattr(history.author, 'name') else None
                    author_display = history.author.displayName if hasattr(history.author, 'displayName') else None
                
                field_change_record = {
                    'change_date': to_iso8601(parse_date(history.created)),
                    'author': author_display or author_name,
                    'changes': non_status_changes
                }
                
                field_changes.append(field_change_record)
        
        # Sort by change date
        field_changes.sort(key=lambda x: x['change_date'])
        
        return field_changes
    
    def _analyze_transition_direction(self, from_status: str, to_status: str) -> Tuple[bool, bool]:
        """
        Analyze whether a status transition is forward or backward in the workflow.
        
        Args:
            from_status: Source status
            to_status: Target status
            
        Returns:
            Tuple of (is_forward_transition, is_backflow)
        """        # Define typical workflow order for backflow detection (case-insensitive)
        workflow_order = {
            # Backlog/planning phase
            'backlog': 1,
            'draft': 2,
            'open': 3,
            'hold': 4,
            'planned': 5,
            
            # Development selection phase - handle legacy names
            'selected for development': 6,
            'to do': 6,  # Legacy name for 'selected for development'
            
            # Development phase
            'do poprawy': 7,
            'in progress': 8,
            'w trakcie': 8,      # Legacy name for 'in progress' 
            'in progress2': 8,   # Legacy name for 'in progress'
            
            # Review phase
            'ready for review': 9,
            'in review': 10,
            
            # Testing phase
            'ready for testing': 11,
            'testy wewnętrzne': 12,
            'testing': 13,
            
            # Approval and release phase
            'do akceptacji klienta': 14,
            'awaiting production release': 15,
            'customer notification': 16,
            
            # Completion phase
            'closed': 17,
            'canceled': 18,
            'completed': 19,
            'done': 20
        }
        
        def get_order(status):
            if not status:
                return 0
            return workflow_order.get(status.lower().strip(), 999)  # Unknown statuses get high number
        
        from_order = get_order(from_status)
        to_order = get_order(to_status)
        
        # Forward transition: moving to higher order number
        is_forward = to_order > from_order
          # Backflow: moving to significantly lower order number (not just adjacent)
        is_backflow = from_order > to_order and (from_order - to_order) > 1
        
        return is_forward, is_backflow
    
    def _is_in_category(self, status: str, status_list: List[str]) -> bool:
        """
        Check if a status is in a given category list (case-insensitive).
        
        Args:
            status: Status name to check
            status_list: List of status names in the category
            
        Returns:
            bool: True if status is in the category
        """
        if not status or not status_list:
            return False
        
        status_lower = status.lower().strip()
        return any(status_lower == cat_status.lower().strip() for cat_status in status_list)
