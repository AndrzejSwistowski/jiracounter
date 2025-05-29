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
    
    def extract_issue_data(self, issue) -> Dict[str, Any]:
        """
        Extract comprehensive data from a JIRA issue.
        
        Args:
            issue: JIRA issue object or dictionary
            
        Returns:
            Dictionary containing extracted issue data
        """
        # Handle both JIRA objects and dictionaries
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
        
        # Extract basic issue information
        issue_data = {
            'key': issue_key,
            'id': issue_id,
            'summary': self.safe_get_field(fields, 'summary'),
            'description': self.safe_get_field(fields, 'description'),
        }
        
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
        
        # Handle dates
        created = self.safe_get_field(fields, 'created')
        updated = self.safe_get_field(fields, 'updated')
        resolved = self.safe_get_field(fields, 'resolutiondate')
        
        issue_data.update({
            'created': to_iso8601(created),
            'updated': to_iso8601(updated),
            'resolved': to_iso8601(resolved),
        })
        
        # Extract assignee information (provide both simple and detailed formats for compatibility)
        assignee = self.safe_get_field(fields, 'assignee')
        if assignee:
            # Use our safe accessor for all object types
            display_name = self.safe_get_field(assignee, 'displayName')
            key = self.safe_get_field(assignee, 'key')
            name = self.safe_get_field(assignee, 'name')
            email_address = self.safe_get_field(assignee, 'emailAddress')
            
            issue_data['assignee'] = {
                'display_name': display_name,
                'key': key,
                'name': name,
                'email_address': email_address
            }
        else:
            issue_data['assignee'] = None
        
        # Extract reporter information (provide both simple and detailed formats for compatibility)
        reporter = self.safe_get_field(fields, 'reporter')
        if reporter:
            # Use our safe accessor for all object types
            display_name = self.safe_get_field(reporter, 'displayName')
            key = self.safe_get_field(reporter, 'key')
            name = self.safe_get_field(reporter, 'name')
            email_address = self.safe_get_field(reporter, 'emailAddress')
            
            issue_data['reporter'] = {
                'display_name': display_name,
                'key': key,
                'name': name,
                'email_address': email_address
            }
        else:
            issue_data['reporter'] = None
        
        # Extract project information
        project = self.safe_get_field(fields, 'project')
        if project:
            # Use our safe accessor for all object types
            project_key = self.safe_get_field(project, 'key')
            project_name = self.safe_get_field(project, 'name')
            project_id = self.safe_get_field(project, 'id')
            
            issue_data['project'] = {
                'key': project_key,
                'name': project_name,
                'id': project_id
            }
        
        # Extract components (provide detailed format for compatibility)
        components = self.safe_get_field(fields, 'components') or []
        issue_data['components'] = []
        if components:
            for comp in components:
                try:
                    # Use our safe accessor for all object types
                    comp_id = self.safe_get_field(comp, 'id')
                    comp_name = self.safe_get_field(comp, 'name')
                    comp_description = self.safe_get_field(comp, 'description')
                    
                    issue_data['components'].append({
                        'id': comp_id,
                        'name': comp_name,
                        'description': comp_description
                    })
                except Exception as e:
                    self.logger.debug(f"Error processing component {comp}: {e}")
                    continue
        
        # Extract labels
        labels = self.safe_get_field(fields, 'labels') or []
        if labels:
            issue_data['labels'] = labels
            
        # Extract parent issue information using the class-level safe_get_field method
        parent = self.safe_get_field(fields, 'parent')
        # Initialize parent_issue to None by default
        issue_data['parent_issue'] = None
        
        if parent:
            # Use the safe_get_field method to extract parent fields consistently
            parent_id = self.safe_get_field(parent, 'id')
            parent_key = self.safe_get_field(parent, 'key')
            
            # Get the parent fields object
            parent_fields = self.safe_get_field(parent, 'fields')
            
            # Get summary from parent fields
            parent_summary = None
            if parent_fields:
                parent_summary = self.safe_get_field(parent_fields, 'summary')
            
            # Set the parent issue data
            issue_data['parent_issue'] = {
                'id': parent_id,
                'key': parent_key,
                'summary': parent_summary
            }
            
            # Log if we have a parent but couldn't get all required information
            if not parent_key and not parent_id:
                self.logger.debug(f"Parent found but couldn't extract key or ID from: {parent}")
        
        # Extract custom fields using field manager - with reduced logging
        try:
            # Only extract custom fields based on issue type
            issue_type_name = issue_data.get('issue_type', '').lower()
            
            # Create a list of relevant fields based on issue type
            # Only attempt to extract fields relevant to specific issue types
            relevant_fields = []
            
            # Most fields are only relevant for stories or epics
            if issue_type_name in ['story', 'epic']:
                relevant_fields.extend(['Epic Link', 'Epic Name', 'Story Points', 'Team', 'Sprint', 'Epic Color'])
            
            # If field IDs are already in cache, proceed with extraction
            # This avoids unnecessary warnings for fields that aren't in the cache
            cached_fields = self.field_manager.field_ids.keys()
            
            # Only extract fields that are either relevant to the issue type or already cached
            for field_name in relevant_fields:
                field_key = field_name.lower().replace(' ', '_')
                if field_key in cached_fields:
                    field_value = self.field_manager.get_field_value(issue if hasattr(issue, 'fields') else None, field_key)
                    if field_value is not None:
                        issue_data[field_key] = field_value
        except Exception as e:
            self.logger.debug(f"Error extracting custom fields: {e}")
        
        # Extract time tracking information
        time_tracking = self.safe_get_field(fields, 'timetracking')
        if time_tracking:
            # Use our safe accessor for all object types
            issue_data['time_tracking'] = {
                'original_estimate': self.safe_get_field(time_tracking, 'originalEstimate'),
                'remaining_estimate': self.safe_get_field(time_tracking, 'remainingEstimate'),
                'time_spent': self.safe_get_field(time_tracking, 'timeSpent'),
                'original_estimate_seconds': self.safe_get_field(time_tracking, 'originalEstimateSeconds'),
                'remaining_estimate_seconds': self.safe_get_field(time_tracking, 'remainingEstimateSeconds'),
                'time_spent_seconds': self.safe_get_field(time_tracking, 'timeSpentSeconds')
            }
        
        # Extract working time metrics
        if created:
            working_minutes = calculate_working_minutes_since_date(created)
            if working_minutes is not None:
                issue_data['working_minutes_since_created'] = working_minutes
        
        # Add legacy fields for backward compatibility
        self._add_legacy_fields(issue_data, issue)
        
        return issue_data
    
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
        
        # Extract legacy allocation fields using the improved allocation extraction method
        try:
            if hasattr(issue, 'fields'):
                # Get rodzaj_pracy value using field manager for allocation information
                rodzaj_pracy_value = self.field_manager.get_field_value(issue, 'rodzaj_pracy')
                
                # Use the improved allocation extraction method
                allocation_value, allocation_code = self._extract_allocation_info(rodzaj_pracy_value)
                
                issue_data['allocation_code'] = allocation_code
                
                # Extract status change date if available
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
