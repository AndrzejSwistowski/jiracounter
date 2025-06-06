"""
Jira Field Manager module for JiraCounter application.

This module provides functionality to manage Jira field IDs and retrieve field values
from Jira issues based on field names.
"""

import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraFieldManager:
    """Manager class for Jira field IDs and value extraction."""
    
    def __init__(self):
        """Initialize the Jira field manager."""
        self.field_ids = {}
    
    @staticmethod
    def safe_get_field(obj, field_name, default=None):
        """Helper function to safely get a field from an object regardless of its type.
        Works with JIRA objects, PropertyHolder objects, and dictionaries.
        
        Args:
            obj: The object to extract a field from
            field_name: The name of the field to extract
            default: Default value to return if the field doesn't exist
            
        Returns:
            The value of the field or the default value
        """
        if obj is None:
            return default
        if hasattr(obj, field_name):  # JIRA object or PropertyHolder
            return getattr(obj, field_name)
        elif isinstance(obj, dict):   # Dictionary
            return obj.get(field_name, default)
        return default
    
    def cache_field_ids(self, jira_client) -> None:
        """Look up and cache custom field IDs for use in Jira operations.
        
        This function populates self.field_ids with the IDs of custom fields
        that are needed for various operations.
        
        Args:
            jira_client: Jira client to use for the operation
        """
        if not jira_client:
            logger.warning("Cannot cache field IDs without a Jira client")
            return
            
        # Look up and cache the "rodzaj pracy" field ID
        rodzaj_pracy_id = self.get_field_id_by_name("rodzaj pracy", jira_client)
        if rodzaj_pracy_id:
            self.field_ids["rodzaj_pracy"] = rodzaj_pracy_id
            logger.debug(f"Found 'rodzaj pracy' field with ID: {rodzaj_pracy_id}")
        else:
            # Fallback to the ID from config if available
            from config import JIRA_CUSTOM_FIELDS
            self.field_ids["rodzaj_pracy"] = JIRA_CUSTOM_FIELDS.get("RODZAJ_PRACY")
            logger.debug(f"Using fallback ID for 'rodzaj pracy' field: {self.field_ids['rodzaj_pracy']}")
            
        # Look up and cache the "data zmiany statusu" field ID
        data_zmiany_statusu_id = self.get_field_id_by_name("data zmiany statusu", jira_client)
        if data_zmiany_statusu_id:
            self.field_ids["data_zmiany_statusu"] = data_zmiany_statusu_id
            logger.debug(f"Found 'data zmiany statusu' field with ID: {data_zmiany_statusu_id}")
        else:
            # Fallback to the ID from config if available
            from config import JIRA_CUSTOM_FIELDS
            self.field_ids["data_zmiany_statusu"] = JIRA_CUSTOM_FIELDS.get("DATA_ZMIANY_STATUSU")
            logger.debug(f"Using fallback ID for 'data zmiany statusu' field: {self.field_ids['data_zmiany_statusu']}")
            
        # Look up and cache the Epic Link field ID
        epic_link_id = self.get_field_id_by_name("Epic Link", jira_client)
        if epic_link_id:
            self.field_ids["epic_link"] = epic_link_id
            logger.debug(f"Found 'Epic Link' field with ID: {epic_link_id}")
        else:
            # Fallback to the ID from config if available
            from config import JIRA_CUSTOM_FIELDS
            self.field_ids["epic_link"] = JIRA_CUSTOM_FIELDS.get("EPIC_LINK")
            logger.debug(f"Using fallback ID for 'Epic Link' field: {self.field_ids['epic_link']}")
    
    def get_field_id_by_name(self, field_name: str, jira_client) -> Optional[str]:
        """Find the custom field ID by its visible name.
        
        Args:
            field_name: The visible name of the field in Jira
            jira_client: Jira client to use for the operation
            
        Returns:
            Optional[str]: The field ID if found, None otherwise
        """
        if not jira_client:
            logger.warning(f"Cannot find field ID for '{field_name}' without a Jira client")
            return None
            
        try:
            fields = jira_client.fields()
            for field in fields:
                if field["name"].lower() == field_name.lower():
                    logger.debug(f"Found field '{field_name}' with ID: {field['id']}")
                    return field["id"]
            
            logger.debug(f"Field '{field_name}' not found in Jira")
            return None
        except Exception as e:
            logger.error(f"Error finding field ID for '{field_name}': {str(e)}")
            return None
            
    # Track which field warnings have already been logged to avoid repeated messages
    _warned_fields = set()
    
    def get_field_value(self, issue, field_name: str) -> Any:
        """Get the value of a field from a Jira issue.
        
        Args:
            issue: Jira issue object
            field_name: The name of the field to get the value for
            
        Returns:
            Any: The value of the field, or None if the field doesn't exist
        """
        if not issue:
            return None
            
        field_id = self.field_ids.get(field_name)
        if not field_id:
            # Get issue key and type for better logging
            issue_key = issue.key if hasattr(issue, 'key') else 'unknown'
            issue_type = issue.fields.issuetype.name if hasattr(issue, 'fields') and hasattr(issue.fields, 'issuetype') else 'unknown'
            
            # Only log warning once per field/issue type combination
            warning_key = f"{field_name}:{issue_type}"
            if warning_key not in self._warned_fields:
                logger.debug(f"Field ID for '{field_name}' not found in cache for issue type '{issue_type}'")
                self._warned_fields.add(warning_key)
            return None
        
        try:
            # First get the fields object regardless of the issue type
            fields = None
            if hasattr(issue, "fields"):
                fields = issue.fields
            elif isinstance(issue, dict) and "fields" in issue:
                fields = issue["fields"]
                
            # Then access the specific field using the ID
            if fields:
                return self.safe_get_field(fields, field_id)
                
            return None
        except Exception as e:
            logger.error(f"Error getting value for field '{field_name}' (ID: {field_id}): {str(e)}")
            return None
