"""
Elasticsearch document formatting utilities.

This module provides classes for formatting Jira data into Elasticsearch documents.
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)

class ElasticsearchDocumentFormatter:
    """
    Handles formatting of Jira data into Elasticsearch documents.
    """
    
    @staticmethod
    def format_changelog_entry(history_record):
        """
        Format a history record for insertion into Elasticsearch.
        
        Args:
            history_record: Dictionary containing the issue history data
            
        Returns:
            Dict containing the formatted data for Elasticsearch
        """
        doc = {
            "historyId": history_record['historyId'],
            "historyDate": history_record['historyDate'],
            "@timestamp": history_record['historyDate'],
            "factType": history_record['factType'],
            "issue": {
                "id": history_record['issueId'],
                "key": history_record['issueKey'],
                "type": {
                    "name": history_record['typeName']
                },
                "status": {
                    "name": history_record['statusName']
                }
            },
            "project": {
                "key": history_record['projectKey'],
                "name": history_record['projectName']
            },
            "author": {
                "username": history_record['authorUserName'],
                "displayName": history_record.get('authorDisplayName')
            }
        }
        
        # Add summary field if it exists
        if history_record.get('summary'):
            doc["summary"] = history_record['summary']
            
        # Add labels if they exist
        if history_record.get('labels'):
            doc["labels"] = history_record['labels']
            
        # Add components if they exist - simplify to store only component names as strings
        if history_record.get('components'):
            try:
                # Extract just the component names
                component_names = []
                
                # Case 1: List of components (could be dicts or strings)
                if isinstance(history_record['components'], list):
                    for comp in history_record['components']:
                        if isinstance(comp, dict) and 'name' in comp:
                            # Extract just the name from component objects
                            component_names.append(comp['name'])
                        elif isinstance(comp, str):
                            # Already a string
                            component_names.append(comp)
                        elif hasattr(comp, '__str__'):
                            # Try to extract name from string representation
                            comp_str = str(comp)
                            if 'name=' in comp_str:
                                try:
                                    name_val = comp_str.split('name=')[1].split(',')[0].strip()
                                    if name_val.endswith('}'):
                                        name_val = name_val[:-1]
                                    component_names.append(name_val)
                                except Exception:
                                    # If parsing fails, use the whole string
                                    component_names.append(comp_str)
                            else:
                                component_names.append(comp_str)
                
                # Case 2: Single component as dict or string
                elif isinstance(history_record['components'], dict):
                    if 'name' in history_record['components']:
                        component_names.append(history_record['components']['name'])
                    else:
                        # If no name field, convert the whole dict to string
                        component_names.append(str(history_record['components']))
                elif isinstance(history_record['components'], str):
                    # Parse string representation if needed
                    comp_str = history_record['components']
                    if 'name=' in comp_str:
                        try:
                            name_val = comp_str.split('name=')[1].split(',')[0].strip()
                            if name_val.endswith('}'):
                                name_val = name_val[:-1]
                            component_names.append(name_val)
                        except Exception:
                            # If parsing fails, use the whole string
                            component_names.append(comp_str)
                    else:
                        component_names.append(comp_str)
                
                # Store the array of component names
                if component_names:
                    doc["components"] = component_names
                    logger.debug(f"Added {len(component_names)} components: {component_names}")
                
            except Exception as e:
                # If all else fails, log the error but don't add the components field
                logger.error(f"Error processing components for {history_record.get('issueKey')}: {e}")
                logger.debug(f"Problematic components data: {history_record.get('components')}")
            
        # Add parent_issue if it exists
        if history_record.get('parent_issue'):
            doc["parent_issue"] = history_record['parent_issue']
            
        # Add epic_issue if it exists
        if history_record.get('epic_issue'):
            doc["epic_issue"] = history_record['epic_issue']
        
        # Add time-based analytics fields if they exist
        if history_record.get('workingDaysFromCreation') is not None:
            doc["workingDaysFromCreation"] = history_record['workingDaysFromCreation']
            
        if history_record.get('workingDaysInStatus') is not None:
            doc["workingDaysInStatus"] = history_record['workingDaysInStatus']
            
        # FIXED: Use workingDaysFromMove as the field name in the document,
        # but look for either workingDaysFromMove or workingDaysFromToDo in the record
        if history_record.get('workingDaysFromMove') is not None:
            doc["workingDaysFromMove"] = history_record['workingDaysFromMove']
        elif history_record.get('workingDaysFromToDo') is not None:
            doc["workingDaysFromMove"] = history_record['workingDaysFromToDo']
        
        # Add optional fields if they exist
        if history_record.get('assigneeUserName'):
            doc["assignee"] = {
                "username": history_record['assigneeUserName'],
                "displayName": history_record.get('assigneeDisplayName')
            }
        
        if history_record.get('reporterUserName'):
            doc["reporter"] = {
                "username": history_record['reporterUserName'],
                "displayName": history_record.get('reporterDisplayName')
            }
        
        if history_record.get('allocationCode'):
            doc["allocation"] = {
                "code": history_record['allocationCode'],
                "name": ElasticsearchDocumentFormatter._get_allocation_name(history_record['allocationCode'])
            }
        
        if history_record.get('parentKey'):
            doc["parentKey"] = history_record['parentKey']
        
        # Add changes if available
        if history_record.get('changes'):
            doc["changes"] = history_record['changes']
        
        return doc
    
    @staticmethod
    def _get_allocation_name(code):
        """
        Get the allocation name from its code.
        
        Args:
            code: The allocation code
            
        Returns:
            str: The allocation name
        """
        allocation_mapping = {
            'NONE': 'No Allocation',
            'NEW': 'New Development',
            'IMPR': 'Improvement',
            'PROD': 'Production',
            'KTLO': 'Keep The Lights On'
        }
        
        return allocation_mapping.get(code, 'Unknown')
