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
                
                "key": history_record['issueKey'],
                "type": {
                    "name": history_record['typeName']
                },
                "status": {
                    "name": history_record['statusName'],
                    "change_date": history_record.get('status_change_date') 
                },
                "created_at": history_record.get('created')
            },
            "project": {
                "key": history_record['projectKey'],
            },
            "author": {
                "displayName": history_record.get('authorDisplayName')
            }
        }
        
        # Add allocation field (as keyword according to mapping)
        if history_record.get('allocationCode'):
            doc["allocation"] = history_record['allocationCode']
        
        # Add summary field with text analysis according to mapping
        if history_record.get('summary'):
            doc["summary"] = history_record['summary']
            
        # Add labels as keyword array according to mapping
        if history_record.get('labels'):
            doc["labels"] = history_record['labels']
            
        # Add components as keyword array according to mapping
        if history_record.get('components'):
            component_names = ElasticsearchDocumentFormatter._extract_component_names(
                history_record.get('components'), 
                history_record.get('issueKey')
            )
            if component_names:
                doc["components"] = component_names
                logger.debug(f"Added {len(component_names)} components: {component_names}")
            
        # Add parent_issue with proper structure according to mapping
        if history_record.get('parent_issue'):
            doc["parent_issue"] = {
                "key": history_record.get('parentKey') or history_record['parent_issue'].get('key'),
                "summary":history_record.get('parent_summary') or history_record['parent_issue'].get('summary')
            }
            
        # Add epic_issue with proper structure according to mapping
        if history_record.get('epic_issue'):
            doc["epic_issue"] = {
                "key": history_record['epic_issue'].get('key'),
                "summary": history_record['epic_issue'].get('summary')
            }
        
        # Add reporter with proper structure according to mapping
        if history_record.get('reporterDisplayName'):
            doc["reporter"] = {
                "displayName": history_record['reporterDisplayName']
            }
        
        # Add time-based fields
        if history_record.get('workingDaysFromCreation') is not None:
            doc["days_since_creation"] = float(history_record['workingDaysFromCreation'])
            
        if history_record.get('todo_exit_date') is not None:
            doc["todo_exit_date"] = history_record['todo_exit_date']
            
        if history_record.get('workingDaysInStatus') is not None:
            doc["days_in_status"] = float(history_record['workingDaysInStatus'])
            
        # Add working_days_from_move_at_point field based on available data
        if history_record.get('working_days_from_move_at_point') is not None:
            doc["working_days_from_move_at_point"] = float(history_record['working_days_from_move_at_point'])
        elif history_record.get('workingDaysFromToDo') is not None:
            doc["working_days_from_move_at_point"] = float(history_record['workingDaysFromToDo'])
        
        # Add assignee with proper structure according to mapping
        if history_record.get('assigneeDisplayName'):
            doc["assignee"] = {
                "displayName": history_record['assigneeDisplayName']
            }
        
        # Add changes as nested objects according to mapping
        if history_record.get('changes'):
            doc["changes"] = history_record['changes']
        
        # Add content text fields with comprehensive text analysis
        if history_record.get('description_text'):
            doc["description_text"] = history_record['description_text']
            
        if history_record.get('comment_text'):
            doc["comment_text"] = history_record['comment_text']
        
        return doc
    
    @staticmethod
    def _extract_component_names(components_data, issue_key=None):
        """
        Extract component names from various data formats.
        
        Args:
            components_data: Component data from Jira (can be list, dict, or string)
            issue_key: Optional issue key for logging purposes
            
        Returns:
            list: List of component names as strings
        """
        component_names = []
        
        try:
            # Case 1: List of components (could be dicts or strings)
            if isinstance(components_data, list):
                for comp in components_data:
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
            elif isinstance(components_data, dict):
                if 'name' in components_data:
                    component_names.append(components_data['name'])
                else:
                    # If no name field, convert the whole dict to string
                    component_names.append(str(components_data))
            elif isinstance(components_data, str):
                # Parse string representation if needed
                comp_str = components_data
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
            
            return component_names
                
        except Exception as e:
            # If all else fails, log the error but don't add the components field
            logger.error(f"Error processing components for {issue_key}: {e}")
            logger.debug(f"Problematic components data: {components_data}")
            return []
    
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
