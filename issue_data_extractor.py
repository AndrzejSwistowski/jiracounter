import logging
from typing import Dict, Any, Optional, List
from time_utils import to_iso8601, calculate_working_minutes_since_date
from jira_field_manager import JiraFieldManager


class IssueDataExtractor:
    """
    Handles extraction of issue data from JIRA issues.
    This class follows the Single Responsibility Principle by focusing solely on data extraction.
    """
    
    def __init__(self, field_manager: JiraFieldManager):
        """
        Initialize the extractor with a field manager.
        
        Args:
            field_manager: JiraFieldManager instance for handling field operations
        """
        self.field_manager = field_manager        
        self.logger = logging.getLogger(__name__)
    
    def extract_issue_data(self, issue) -> Dict[str, Any]:
        """
        Extract comprehensive data from a JIRA issue.
        
        This method serves as a template method that coordinates the extraction process,
        delegating to specialized methods for each type of data.
        
        Args:
            issue: JIRA issue object or dictionary
            
        Returns:
            Dictionary containing extracted issue data with the following structure:
            
            {
                # Basic information
                'key': 'PROJECT-123',       # JIRA issue key
                'id': '12345',              # JIRA issue ID
                'summary': 'Issue title',   # Issue summary
                'description': 'Details',   # Issue description text
                
                # Type and status information
                'issue_type': 'Story',      # Issue type name
                'status': 'In Progress',    # Current status
                'priority': 'High',         # Priority level
                'resolution': 'Done',       # Resolution if resolved
                
                # Date fields (ISO 8601 format strings)
                'created': '2023-01-01T10:00:00+00:00',    # Creation date
                'updated': '2023-01-15T14:30:00+00:00',    # Last update date
                'resolved': '2023-01-20T16:00:00+00:00',   # Resolution date
                
                # People information
                'assignee': {               # Assigned user (or None)
                    'display_name': 'John Doe',
                    'key': 'jdoe',
                    'name': 'jdoe',
                    'email_address': 'jdoe@example.com'
                },
                'reporter': {               # Reporter user (or None)
                    'display_name': 'Jane Smith',
                    'key': 'jsmith',
                    'name': 'jsmith',
                    'email_address': 'jsmith@example.com'
                },
                
                # Project information
                'project': {                # Project data
                    'key': 'PROJECT',
                    'name': 'Project Name',
                    'id': '10000'
                },
                
                # Components and labels
                'components': [             # List of components
                    {
                        'id': '1001',
                        'name': 'Frontend',
                        'description': 'UI components'
                    },
                    {
                        'id': '1002',
                        'name': 'API',
                        'description': 'Backend API'
                    }
                ],
                'labels': ['label1', 'label2'],  # List of labels
                
                # Parent issue information (if available, otherwise None)
                'parent_issue': {
                    'id': '12344',
                    'key': 'PROJECT-122',
                    'summary': 'Parent Issue'
                },

                'epic_issue': {'key': 'PROJECT-100', 'name': 'Feature Epic'},

                # Custom fields (only for specific issue types)
                'epic_link': 'PROJECT-100',     # For stories: link to epic
                'epic_name': 'Feature Epic',    # For epics: epic name
                'story_points': 5,              # For stories: estimation points
                'team': 'Team A',               # Team assignment
                'sprint': 'Sprint 5',           # Current sprint
                'epic_color': 'green',          # For epics: color
                
                # Time tracking
                'time_tracking': {
                    'original_estimate': '2d',
                    'remaining_estimate': '1d',
                    'time_spent': '1d',
                    'original_estimate_seconds': 57600,
                    'remaining_estimate_seconds': 28800,
                    'time_spent_seconds': 28800
                },
                
                # Working time metrics
                'working_minutes_since_created': 4800,  # Working minutes since creation
                  # Work type information
                'allocation_code': 'NEW',       # Valid values: NEW, IMPR, PROD, KTLO
                
                # Legacy fields (for backward compatibility)
                'type': 'Story',                # Same as 'issue_type'
                'assignee_display_name': 'John Doe',
                'reporter_display_name': 'Jane Smith',
                'component_names': ['Frontend', 'API'],
                'minutes_since_creation': 4800,  # Same as 'working_minutes_since_created'
                'status_change_date': '2023-01-10T09:00:00+00:00'
            }
            
            Note: Some fields may be None or missing if the data is not available
            in the original issue object.
        """
        # Get fields and basic identifiers 
        fields, issue_key, issue_id = self._extract_issue_fields(issue)
        
        # Create result dictionary with base data
        issue_data = self._extract_base_fields(fields, issue_key, issue_id)
          # Extract each type of data through dedicated methods
        self._extract_type_and_status_fields(fields, issue_data)
        self._extract_date_fields(fields, issue_data)
        self._extract_people_fields(fields, issue_data)
        self._extract_project_info(fields, issue_data)
        self._extract_components(fields, issue_data)
        self._extract_labels(fields, issue_data)
        self._extract_parent_issue(fields, issue_data)
        self._extract_custom_fields(issue, fields, issue_data)
        self._extract_time_tracking(fields, issue_data)
        self._extract_working_time_metrics(fields, issue_data)
        
        # Extract allocation code (not a legacy field)
        allocation_code = self._extract_allocation_code(issue)
        if allocation_code:
            issue_data['allocation_code'] = allocation_code
        
        # Add legacy fields for backward compatibility
        self._add_legacy_fields(issue_data, issue)
        
        return issue_data
    
    def _extract_issue_fields(self, issue) -> tuple:
        """Extract fields object and basic identifiers based on issue type."""
        if hasattr(issue, 'fields'):
            # JIRA issue object - could be normal JIRA object or PropertyHolder
            fields = issue.fields
            issue_key = self.safe_get_field(issue, 'key')
            issue_id = self.safe_get_field(issue, 'id')
        elif isinstance(issue, dict):
            # Dictionary format
            fields = issue.get('fields', {})
            issue_key = issue.get('key')
            issue_id = issue.get('id')
        else:
            # Unknown object type, try best effort extraction
            fields = self.safe_get_field(issue, 'fields', {})
            issue_key = self.safe_get_field(issue, 'key', str(issue))
            issue_id = self.safe_get_field(issue, 'id')
        
        return fields, issue_key, issue_id
    
    def _extract_base_fields(self, fields, issue_key, issue_id) -> Dict[str, Any]:
        """Extract the basic issue information."""
        return {
            'key': issue_key,
            'id': issue_id,
            'summary': self.safe_get_field(fields, 'summary'),
            'description': self.safe_get_field(fields, 'description'),
        }
    
    def _extract_type_and_status_fields(self, fields, issue_data) -> None:
        """Extract issue type, status, priority and resolution fields."""
        # Handle issue type
        issuetype = self.safe_get_field(fields, 'issuetype')
        if issuetype:
            issue_data['issue_type'] = self.safe_get_field(issuetype, 'name')
        
        # Handle status
        status = self.safe_get_field(fields, 'status')
        if status:
            issue_data['status'] = self.safe_get_field(status, 'name')
        
        # Handle priority
        priority = self.safe_get_field(fields, 'priority')
        if priority:
            issue_data['priority'] = self.safe_get_field(priority, 'name')
        
        # Handle resolution
        resolution = self.safe_get_field(fields, 'resolution')
        if resolution:
            issue_data['resolution'] = self.safe_get_field(resolution, 'name')
    
    def _extract_date_fields(self, fields, issue_data) -> None:
        """Extract and format date fields."""
        created = self.safe_get_field(fields, 'created')
        updated = self.safe_get_field(fields, 'updated')
        resolved = self.safe_get_field(fields, 'resolutiondate')
        
        issue_data.update({
            'created': to_iso8601(created),
            'updated': to_iso8601(updated),
            'resolved': to_iso8601(resolved),
        })
    
    def _extract_people_fields(self, fields, issue_data) -> None:
        """Extract assignee and reporter information."""
        # Extract assignee
        assignee = self.safe_get_field(fields, 'assignee')
        if assignee:
            issue_data['assignee'] = self._extract_user_info(assignee)
        else:
            issue_data['assignee'] = None
        
        # Extract reporter
        reporter = self.safe_get_field(fields, 'reporter')
        if reporter:
            issue_data['reporter'] = self._extract_user_info(reporter)
        else:
            issue_data['reporter'] = None
    
    def _extract_user_info(self, user_obj) -> Dict[str, str]:
        """Extract standard user information from a user object."""
        return {
            'display_name': self.safe_get_field(user_obj, 'displayName'),
            'key': self.safe_get_field(user_obj, 'key'),
            'name': self.safe_get_field(user_obj, 'name'),
            'email_address': self.safe_get_field(user_obj, 'emailAddress')
        }
    
    def _extract_project_info(self, fields, issue_data) -> None:
        """Extract project information."""
        project = self.safe_get_field(fields, 'project')
        if project:
            issue_data['project'] = {
                'key': self.safe_get_field(project, 'key'),
                'name': self.safe_get_field(project, 'name'),
                'id': self.safe_get_field(project, 'id')
            }
    
    def _extract_components(self, fields, issue_data) -> None:
        """Extract components information."""
        components = self.safe_get_field(fields, 'components') or []
        issue_data['components'] = []
        
        if components:
            for comp in components:
                try:
                    comp_data = {
                        'id': self.safe_get_field(comp, 'id'),
                        'name': self.safe_get_field(comp, 'name'),
                        'description': self.safe_get_field(comp, 'description')
                    }
                    issue_data['components'].append(comp_data)
                except Exception as e:
                    self.logger.debug(f"Error processing component {comp}: {e}")
    
    def _extract_labels(self, fields, issue_data) -> None:
        """Extract and normalize labels."""
        try:
            labels = self.safe_get_field(fields, 'labels') or []
            
            # Normalize labels to always be a list
            if labels:
                if not isinstance(labels, list):
                    try:
                        issue_data['labels'] = list(labels) if hasattr(labels, '__iter__') else [str(labels)]
                    except Exception as e:
                        self.logger.debug(f"Error converting labels to list: {e}")
                        issue_data['labels'] = [str(labels)]
                else:
                    issue_data['labels'] = labels
            else:
                issue_data['labels'] = []
        except Exception as e:
            self.logger.debug(f"Error processing labels: {e}")
            issue_data['labels'] = []
    
    def _extract_parent_issue(self, fields, issue_data) -> None:
        """Extract parent issue information if available."""
        parent = self.safe_get_field(fields, 'parent')
        issue_data['parent_issue'] = None
        
        if parent:
            parent_id = self.safe_get_field(parent, 'id')
            parent_key = self.safe_get_field(parent, 'key')
            parent_fields = self.safe_get_field(parent, 'fields')
            
            parent_summary = None
            if parent_fields:
                parent_summary = self.safe_get_field(parent_fields, 'summary')
            
            issue_data['parent_issue'] = {
                'id': parent_id,
                'key': parent_key,
                'summary': parent_summary
            }
            
            # Log if we have a parent but couldn't get all required information
            if not parent_key and not parent_id:
                self.logger.debug(f"Parent found but couldn't extract key or ID from: {parent}")
    
    def _extract_custom_fields(self, issue, fields, issue_data) -> None:
        """Extract custom fields based on issue type."""
        try:
            # Only extract custom fields based on issue type
            issue_type_name = issue_data.get('issue_type', '').lower()
            relevant_fields = []
            
            # Most fields are only relevant for stories or epics
            if issue_type_name in ['story', 'epic']:
               relevant_fields.extend(['Epic Link', 'Epic Name', 'Story Points', 'Team', 'Sprint', 'Epic Color'])
            
            # Get cached fields to avoid unnecessary warnings
            cached_fields = self.field_manager.field_ids.keys()
            
            # Extract only cached relevant fields
            for field_name in relevant_fields:
                field_key = field_name.lower().replace(' ', '_')
                if field_key in cached_fields:
                    field_value = self.field_manager.get_field_value(
                        issue if hasattr(issue, 'fields') else None, 
                        field_key
                    )
                    if field_value is not None:
                        issue_data[field_key] = field_value
        except Exception as e:
            self.logger.debug(f"Error extracting custom fields: {e}")
    
    def _extract_time_tracking(self, fields, issue_data) -> None:
        """Extract time tracking information."""
        time_tracking = self.safe_get_field(fields, 'timetracking')
        if time_tracking:
            issue_data['time_tracking'] = {
                'original_estimate': self.safe_get_field(time_tracking, 'originalEstimate'),
                'remaining_estimate': self.safe_get_field(time_tracking, 'remainingEstimate'),
                'time_spent': self.safe_get_field(time_tracking, 'timeSpent'),
                'original_estimate_seconds': self.safe_get_field(time_tracking, 'originalEstimateSeconds'),
                'remaining_estimate_seconds': self.safe_get_field(time_tracking, 'remainingEstimateSeconds'),
                'time_spent_seconds': self.safe_get_field(time_tracking, 'timeSpentSeconds')
            }
    
    def _extract_working_time_metrics(self, fields, issue_data) -> None:
        """Calculate and extract working time metrics."""
        created = self.safe_get_field(fields, 'created')
        if created:
            working_minutes = calculate_working_minutes_since_date(created)
            if working_minutes is not None:
                issue_data['working_minutes_since_created'] = working_minutes
    
    def _add_legacy_fields(self, issue_data: Dict[str, Any], issue) -> None:
        """
        Add legacy fields to maintain backward compatibility.
        
        Args:
            issue_data: The extracted issue data dictionary
            issue: The original JIRA issue object
        """
        # Map new field names to legacy field names
        if 'issue_type' in issue_data:
            issue_data['type'] = issue_data['issue_type']
        
        # Add simple string format for assignee/reporter (original format compatibility)
        if 'assignee' in issue_data and issue_data['assignee']:
            issue_data['assignee_display_name'] = issue_data['assignee'].get('display_name')
        
        if 'reporter' in issue_data and issue_data['reporter']:
            issue_data['reporter_display_name'] = issue_data['reporter'].get('display_name')
          
        # Add simple component names list (original format compatibility)
        if 'components' in issue_data and issue_data['components']:
            try:
                issue_data['component_names'] = [comp.get('name') for comp in issue_data['components'] if isinstance(comp, dict) and comp.get('name')]
            except Exception as e:
                self.logger.debug(f"Error creating component_names: {e}")
                issue_data['component_names'] = []
        
        # Add working minutes field with legacy name
        if 'working_minutes_since_created' in issue_data:
            issue_data['minutes_since_creation'] = issue_data['working_minutes_since_created']
          # Extract status change date if available (legacy field)
        try:
            if hasattr(issue, 'fields'):
                status_change_date = None
                data_zmiany_statusu_value = self.field_manager.get_field_value(issue, 'data_zmiany_statusu')
                if data_zmiany_statusu_value:
                    try:
                        status_change_date = to_iso8601(data_zmiany_statusu_value)
                    except (ValueError, TypeError):
                        self.logger.debug(f"Could not parse 'data zmiany statusu' date: {data_zmiany_statusu_value}")
                
                issue_data['status_change_date'] = status_change_date
                
        except Exception as e:
            self.logger.debug(f"Error adding legacy fields: {e}")
    
    def _extract_allocation_info(self, rodzaj_pracy_value=None) -> tuple:
        """Extract allocation value and code from the rodzaj_pracy (work type) field.
        
        This method processes the JIRA custom field 'rodzaj_pracy' which contains
        allocation information in the format "Description [CODE]".
        
        Args:
            rodzaj_pracy_value: The value of the rodzaj_pracy field (CustomFieldOption or string)
            
        Returns:
            tuple: (allocation_value, allocation_code) where:
                - allocation_value: Full text of the allocation option
                - allocation_code: Extracted code from brackets (e.g., "DEV" from "Development [DEV]")
        """
        allocation_value = None
        allocation_code = None
        
        # Extract the string value from the field
        if rodzaj_pracy_value is not None:
            # Check if rodzaj_pracy is a CustomFieldOption object
            if hasattr(rodzaj_pracy_value, 'value'):
                allocation_value = rodzaj_pracy_value.value
            elif isinstance(rodzaj_pracy_value, str):
                allocation_value = rodzaj_pracy_value
          # Extract the code from brackets if the format is "Something [CODE]"
        if allocation_value and '[' in allocation_value and ']' in allocation_value:
            try:
                allocation_code = allocation_value.split('[')[1].split(']')[0]
            except (IndexError, AttributeError):
                self.logger.debug(f"Could not extract allocation code from value: {allocation_value}")
        
        return allocation_value, allocation_code
        
    def _extract_allocation_code(self, issue) -> str:
        """
        Extract and validate the allocation code from the issue.
        
        Valid allocation codes are: NEW, IMPR, PROD, KTLO
        
        Args:
            issue: The JIRA issue object
            
        Returns:
            str: The extracted and validated allocation code, or None if not found or invalid
        """
        if not hasattr(issue, 'fields'):
            return None
            
        # Get rodzaj_pracy value using field manager for allocation information
        rodzaj_pracy_value = self.field_manager.get_field_value(issue, 'rodzaj_pracy')
        if rodzaj_pracy_value:
            # Extract allocation info
            allocation_value, allocation_code = self._extract_allocation_info(rodzaj_pracy_value)

            valid_codes = ['NEW', 'IMPR', 'PROD', 'KTLO']
            if allocation_code in valid_codes:
                return allocation_code
            else:
                self.logger.warning(f"Invalid allocation code: {allocation_code}. Must be one of {valid_codes}")
        return None

    def epic_enricher(self, issue_data: Dict[str, Any], delegate_get_issue) -> None:
        """
        Enrich issue data with epic information by checking current issue and parent hierarchy.
        
        This function recursively searches for epic information by:
        1. First checking if the current issue has epic_name (for epic issues)
        2. If no epic found, checking parent issues recursively up the hierarchy
        3. Using the delegate function to fetch parent issue data when needed
        
        Args:
            issue_data: The issue data dictionary to enrich
            delegate_get_issue: Function that takes issue_key and returns issue_data
        """
        try:
            # First check if this issue already has epic information
            if self._has_epic_info(issue_data):
                self.logger.debug(f"Issue {issue_data.get('key')} already has epic information")
                return
            
            # Check if current issue is an epic itself (has epic_name)
            if self._extract_epic_from_current_issue(issue_data):
                self.logger.debug(f"Issue {issue_data.get('key')} is an epic itself")
                return
            
            # If no epic found, check parent hierarchy
            self._check_parent_for_epic(issue_data, delegate_get_issue, max_depth=5)
            
        except Exception as e:
            self.logger.error(f"Error in epic_enricher for issue {issue_data.get('key', 'unknown')}: {str(e)}")
    
    def _has_epic_info(self, issue_data: Dict[str, Any]) -> bool:
        """Check if issue already has epic information."""
        epic_issue = issue_data.get('epic_issue')
        return epic_issue is not None and epic_issue.get('key') is not None
    
    def _extract_epic_from_current_issue(self, issue_data: Dict[str, Any]) -> bool:
        """
        Check if current issue is an epic and create epic_issue object if it has epic_name.
        
        Returns:
            bool: True if epic information was extracted, False otherwise
        """
        epic_name = issue_data.get('epic_name')
        if epic_name or issue_data.get('issue_type', '').lower() == 'epic':
            # This issue is an epic, create epic_issue object pointing to itself
            issue_data['epic_issue'] = {
                'key': issue_data.get('key'),
                'id': issue_data.get('id'),
                'name': epic_name or issue_data.get('summary'),
                'summary': issue_data.get('summary')
            }
            self.logger.debug(f"Issue {issue_data.get('key')} is an epic with name: {epic_name}")
            return True
        return False
    
    def _check_parent_for_epic(self, issue_data: Dict[str, Any], delegate_get_issue, max_depth: int = 5) -> bool:
        """
        Recursively check parent issues for epic information.
        
        Args:
            issue_data: Current issue data
            delegate_get_issue: Function to get issue data by key
            max_depth: Maximum recursion depth to prevent infinite loops
            
        Returns:
            bool: True if epic information was found and set, False otherwise
        """
        if max_depth <= 0:
            self.logger.warning(f"Max depth reached while searching for epic in parent hierarchy for {issue_data.get('key')}")
            return False
        
        parent_issue = issue_data.get('parent_issue')
        if not parent_issue or not parent_issue.get('key'):
            self.logger.debug(f"No parent issue found for {issue_data.get('key')}")
            return False
        
        parent_key = parent_issue.get('key')
        self.logger.debug(f"Checking parent issue {parent_key} for epic information")
        
        try:
            # Get parent issue data using the delegate
            parent_data = delegate_get_issue(parent_key)
            if not parent_data:
                self.logger.warning(f"Could not retrieve parent issue data for {parent_key}")
                return False
            
            # Check if parent has epic information we can inherit
            if self._copy_epic_from_parent(issue_data, parent_data):
                return True
            
            # If parent doesn't have epic info, check if parent is an epic itself
            if self._extract_epic_from_current_issue(parent_data):
                # Copy the epic info from parent to current issue
                issue_data['epic_issue'] = parent_data.get('epic_issue')
                self.logger.debug(f"Inherited epic from parent epic {parent_key}")
                return True
            
            # Recursively check parent's parent
            return self._check_parent_for_epic(parent_data, delegate_get_issue, max_depth - 1)
            
        except Exception as e:
            self.logger.error(f"Error checking parent {parent_key} for epic info: {str(e)}")
            return False
    
    def _copy_epic_from_parent(self, issue_data: Dict[str, Any], parent_data: Dict[str, Any]) -> bool:
        """
        Copy epic information from parent to current issue if parent has it.
        
        Returns:
            bool: True if epic info was copied, False otherwise
        """
        parent_epic = parent_data.get('epic_issue')
        if parent_epic and parent_epic.get('key'):
            issue_data['epic_issue'] = {
                'key': parent_epic.get('key'),
                'id': parent_epic.get('id'),
                'name': parent_epic.get('name'),
                'summary': parent_epic.get('summary')
            }
            self.logger.debug(f"Copied epic {parent_epic.get('key')} from parent {parent_data.get('key')}")
            return True
        return False

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