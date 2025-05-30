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
        
        Args:
            issue: JIRA issue object or dictionary
            
        Returns:
            Dictionary containing extracted issue data
        """
        # Handle both JIRA objects and dictionaries
        if hasattr(issue, 'fields'):
            # JIRA issue object
            fields = issue.fields
            issue_key = issue.key
            issue_id = issue.id
        else:
            # Dictionary format
            fields = issue.get('fields', {})
            issue_key = issue.get('key')
            issue_id = issue.get('id')
        
        # Extract basic issue information
        issue_data = {
            'key': issue_key,
            'id': issue_id,
            'summary': getattr(fields, 'summary', None) if hasattr(fields, 'summary') else fields.get('summary'),
            'description': getattr(fields, 'description', None) if hasattr(fields, 'description') else fields.get('description'),
        }
        
        # Handle issue type
        issuetype = getattr(fields, 'issuetype', None) if hasattr(fields, 'issuetype') else fields.get('issuetype')
        if issuetype:
            issue_data['issue_type'] = getattr(issuetype, 'name', None) if hasattr(issuetype, 'name') else issuetype.get('name')
        
        # Handle status
        status = getattr(fields, 'status', None) if hasattr(fields, 'status') else fields.get('status')
        if status:
            issue_data['status'] = getattr(status, 'name', None) if hasattr(status, 'name') else status.get('name')
        
        # Handle priority
        priority = getattr(fields, 'priority', None) if hasattr(fields, 'priority') else fields.get('priority')
        if priority:
            issue_data['priority'] = getattr(priority, 'name', None) if hasattr(priority, 'name') else priority.get('name')
        
        # Handle resolution
        resolution = getattr(fields, 'resolution', None) if hasattr(fields, 'resolution') else fields.get('resolution')
        if resolution:
            issue_data['resolution'] = getattr(resolution, 'name', None) if hasattr(resolution, 'name') else resolution.get('name')
        
        # Handle dates
        created = getattr(fields, 'created', None) if hasattr(fields, 'created') else fields.get('created')
        updated = getattr(fields, 'updated', None) if hasattr(fields, 'updated') else fields.get('updated')
        resolved = getattr(fields, 'resolutiondate', None) if hasattr(fields, 'resolutiondate') else fields.get('resolutiondate')
        
        issue_data.update({
            'created': to_iso8601(created),
            'updated': to_iso8601(updated),
            'resolved': to_iso8601(resolved),
        })        # Extract assignee information (provide both simple and detailed formats for compatibility)
        assignee = getattr(fields, 'assignee', None) if hasattr(fields, 'assignee') else fields.get('assignee')
        if assignee:
            # Check if this is a JIRA object or dictionary
            if hasattr(assignee, 'displayName'):
                # JIRA object
                display_name = assignee.displayName
                key = getattr(assignee, 'key', None)
                name = getattr(assignee, 'name', None)
                email_address = getattr(assignee, 'emailAddress', None)
            else:
                # Dictionary
                display_name = assignee.get('displayName')
                key = assignee.get('key')
                name = assignee.get('name')
                email_address = assignee.get('emailAddress')
            
            issue_data['assignee'] = {
                'display_name': display_name,
                'key': key,
                'name': name,
                'email_address': email_address
            }
        else:
            issue_data['assignee'] = None
        
        # Extract reporter information (provide both simple and detailed formats for compatibility)
        reporter = getattr(fields, 'reporter', None) if hasattr(fields, 'reporter') else fields.get('reporter')
        if reporter:
            # Check if this is a JIRA object or dictionary
            if hasattr(reporter, 'displayName'):
                # JIRA object
                display_name = reporter.displayName
                key = getattr(reporter, 'key', None)
                name = getattr(reporter, 'name', None)
                email_address = getattr(reporter, 'emailAddress', None)
            else:
                # Dictionary
                display_name = reporter.get('displayName')
                key = reporter.get('key')
                name = reporter.get('name')
                email_address = reporter.get('emailAddress')
            
            issue_data['reporter'] = {
                'display_name': display_name,
                'key': key,
                'name': name,
                'email_address': email_address
            }
        else:
            issue_data['reporter'] = None
          # Extract project information
        project = getattr(fields, 'project', None) if hasattr(fields, 'project') else fields.get('project')
        if project:
            # Check if this is a JIRA object or dictionary
            if hasattr(project, 'key'):
                # JIRA object
                issue_data['project'] = {
                    'key': project.key,
                    'name': getattr(project, 'name', None),
                    'id': getattr(project, 'id', None)
                }
            else:
                # Dictionary
                issue_data['project'] = {
                    'key': project.get('key'),
                    'name': project.get('name'),
                    'id': project.get('id')
                }        # Extract components (provide detailed format for compatibility)
        components = getattr(fields, 'components', []) if hasattr(fields, 'components') else fields.get('components', [])
        issue_data['components'] = []
        if components:
            for comp in components:
                try:
                    # Check if this is a JIRA object or dictionary
                    if hasattr(comp, 'name'):
                        # JIRA object
                        issue_data['components'].append({
                            'id': getattr(comp, 'id', None),
                            'name': comp.name,
                            'description': getattr(comp, 'description', None)
                        })
                    elif isinstance(comp, dict):
                        # Dictionary
                        issue_data['components'].append({
                            'id': comp.get('id'),
                            'name': comp.get('name'),
                            'description': comp.get('description')
                        })
                except Exception as e:
                    self.logger.debug(f"Error processing component {comp}: {e}")
                    continue
        
        # Extract labels
        labels = getattr(fields, 'labels', []) if hasattr(fields, 'labels') else fields.get('labels', [])
        if labels:
            issue_data['labels'] = labels        # Extract parent issue information (match original simple approach)
        parent = getattr(fields, 'parent', None) if hasattr(fields, 'parent') else fields.get('parent')
        if parent:
            # Check if this is a JIRA object or dictionary
            if hasattr(parent, 'key'):
                # JIRA object
                parent_fields = getattr(parent, 'fields', None)
                issue_data['parent_issue'] = {
                    'id': getattr(parent, 'id', None),
                    'key': parent.key,
                    'summary': getattr(parent_fields, 'summary', None) if parent_fields else None
                }
            else:
                # Dictionary
                parent_fields = parent.get('fields', {})
                issue_data['parent_issue'] = {
                    'id': parent.get('id'),
                    'key': parent.get('key'),
                    'summary': parent_fields.get('summary') if isinstance(parent_fields, dict) else None
                }
        
        # Extract custom fields using field manager
        try:
            # Extract epic information
            epic_link = self.field_manager.get_field_value(issue if hasattr(issue, 'fields') else None, 'Epic Link')
            if epic_link:
                issue_data['epic_link'] = epic_link
                
                # Extract full epic issue information if epic link exists
                issue_data['epic_issue'] = self._extract_epic_issue_info(epic_link)
            
            epic_name = self.field_manager.get_field_value(issue if hasattr(issue, 'fields') else None, 'Epic Name')
            if epic_name:
                issue_data['epic_name'] = epic_name
            
            # Extract story points
            story_points = self.field_manager.get_field_value(issue if hasattr(issue, 'fields') else None, 'Story Points')
            if story_points is not None:
                issue_data['story_points'] = story_points
            
            # Extract custom fields using field manager
            for custom_field_name in ['Team', 'Sprint', 'Epic Color']:
                field_value = self.field_manager.get_field_value(issue if hasattr(issue, 'fields') else None, custom_field_name)
                if field_value is not None:
                    issue_data[custom_field_name.lower().replace(' ', '_')] = field_value
        except Exception as e:
            self.logger.debug(f"Error extracting custom fields: {e}")
        return issue_data        
    
    def _extract_epic_issue_info(self, epic_link):
        """
        Extract complete epic issue information from an epic link.
        
        Args:
            epic_link: The epic link value (could be epic key or epic object)
            
        Returns:
            Dictionary containing epic issue information or None if extraction fails
        """
        try:
            # If epic_link is already a string (epic key), we can try to fetch it
            # If it's an object, we need to extract the key first
            epic_key = None
            
            if isinstance(epic_link, str):
                epic_key = epic_link
            elif hasattr(epic_link, 'key'):
                epic_key = epic_link.key
            elif hasattr(epic_link, 'value'):
                epic_key = epic_link.value
            elif isinstance(epic_link, dict):
                epic_key = epic_link.get('key')
            
            if not epic_key:
                self.logger.debug(f"Could not extract epic key from epic_link: {epic_link}")
                return None
            
            # For now, return basic epic info. In a full implementation, you might want to 
            # inject a JiraService instance to fetch the complete epic details
            epic_issue = {
                'key': epic_key,
                'id': None,  # Would need to fetch from JIRA
                'summary': None  # Would need to fetch from JIRA
            }
            
            self.logger.debug(f"Extracted epic issue info for key: {epic_key}")
            return epic_issue
            
        except Exception as e:
            self.logger.debug(f"Error extracting epic issue info from {epic_link}: {e}")
            return None
    
    def _add_legacy_fields(self, issue_data: Dict[str, Any], issue) -> None:
        """
        Add legacy fields to maintain backward compatibility.
        
        Args:
            issue_data: The extracted issue data dictionary
            issue: The original JIRA issue object
        """        # Map new field names to legacy field names
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
                
                # Keep legacy field name 'backet' for backward compatibility
                issue_data['backet'] = allocation_value
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