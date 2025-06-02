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
    
    @staticmethod
    def format_issue_record(issue_record):
        """
        Format an issue record for insertion into Elasticsearch.
        This method handles the issue record structure that contains
        all issue data, metrics, and history in a single record per issue.
        
        Args:
            issue_record: Dictionary containing the issue data
                         with keys: issue_data, issue_description, issue_comments,
                         metrics, status_transitions, field_changes
            
        Returns:
            Dict containing the formatted data for Elasticsearch
        """        
        from time_utils import format_working_minutes_to_text
        issue_data = issue_record.get('issue_data', {})
        metrics = issue_record.get('metrics', {})
        status_transitions = issue_record.get('status_transitions', [])
        field_changes = issue_record.get('field_changes', [])
        doc = {
            "@timestamp": issue_data.get('updated'),
            "issue": {
                "id": issue_data.get('issueId'),
                "key": issue_data.get('key'),
                "type": {"name": issue_data.get('type') or issue_data.get('typeName')},
                "status": {
                    "name": issue_data.get('status') or issue_data.get('statusName'),
                    "change_at": issue_data.get('status_change_date'),
                    "working_minutes": metrics.get('working_minutes_in_current_status'),
                    "working_days": int(metrics.get('working_minutes_in_current_status', 0) / (60 * 8)) if metrics.get('working_minutes_in_current_status') else None,
                    "period": format_working_minutes_to_text(metrics.get('working_minutes_in_current_status'))
                },
                "created_at": issue_data.get('created'),
                "working_minutes": metrics.get('working_minutes_from_create'),
                "working_days": int(metrics.get('working_minutes_from_create', 0) / (60 * 8)) if metrics.get('working_minutes_from_create') else None,
                "period": format_working_minutes_to_text(metrics.get('working_minutes_from_create'))
            },
            "project": {"key": issue_data.get('project_key') or issue_data.get('projectKey')},
        }
        # Optional fields
        if issue_data.get('allocation_code') or issue_data.get('allocationCode'):
            doc["allocation"] = issue_data.get('allocation_code') or issue_data.get('allocationCode')
        if issue_data.get('labels'):
            doc["labels"] = issue_data['labels']
        if issue_data.get('components'):
            doc["components"] = [c['name'] if isinstance(c, dict) and 'name' in c else c for c in issue_data['components']]
        if issue_data.get('summary'):
            doc["summary"] = issue_data['summary']
        if issue_data.get('parent_issue'):
            doc["parent_issue"] = {
                "key": issue_data['parent_issue'].get('key'),
                "summary": issue_data['parent_issue'].get('summary')
            }
        if issue_data.get('epic_issue'):
            doc["epic_issue"] = {
                "key": issue_data['epic_issue'].get('key'),
                "summary": issue_data['epic_issue'].get('name') or issue_data['epic_issue'].get('summary')
            }
        if issue_data.get('reporter'):
            doc["reporter"] = {"displayName": issue_data['reporter'].get('display_name') or issue_data['reporter'].get('displayName')}
        if issue_data.get('assignee'):
            doc["assignee"] = {"displayName": issue_data['assignee'].get('display_name') or issue_data['assignee'].get('displayName')}        # Content fields
        if issue_record.get('issue_description'):
            doc["description"] = issue_record['issue_description']
        if issue_record.get('issue_comments'):
            comments = issue_record['issue_comments']
            if isinstance(comments, list) and comments:
                comment_texts = [c['body'] for c in comments if isinstance(c, dict) and c.get('body')]
                if comment_texts:
                    doc["comment"] = " ".join(comment_texts)
        # Metrics: categorized time
        if metrics.get('backlog_minutes') is not None:
            doc["backlog"] = {
                "working_minutes": metrics['backlog_minutes'],
                "working_days": int(metrics['backlog_minutes'] / (60 * 8)),
                "period": format_working_minutes_to_text(metrics['backlog_minutes'])
            }
        if metrics.get('processing_minutes') is not None:
            doc["processing"] = {
                "working_minutes": metrics['processing_minutes'],
                "working_days": int(metrics['processing_minutes'] / (60 * 8)),
                "period": format_working_minutes_to_text(metrics['processing_minutes'])
            }
        if metrics.get('waiting_minutes') is not None:
            doc["waiting"] = {
                "working_minutes": metrics['waiting_minutes'],
                "working_days": int(metrics['waiting_minutes'] / (60 * 8)),
                "period": format_working_minutes_to_text(metrics['waiting_minutes'])
            }
        # Metrics: development selection
        if metrics.get('todo_exit_date') is not None:
            doc["selected_for_development_at"] = metrics['todo_exit_date']
        if metrics.get('working_minutes_from_first_move') is not None:
            doc["from_selected_for_development"] = {
                "working_minutes": metrics['working_minutes_from_first_move'],
                "working_days": int(metrics['working_minutes_from_first_move'] / (60 * 8)),
                "period": format_working_minutes_to_text(metrics['working_minutes_from_first_move'])
            }
        # Metrics: status transitions
        if metrics.get('total_transitions') is not None:
            doc["total_transitions"] = metrics['total_transitions']
        if metrics.get('backflow_count') is not None:
            doc["backflow_count"] = metrics['backflow_count']
        if metrics.get('unique_statuses_visited'):
            doc["unique_statuses_visited"] = metrics['unique_statuses_visited']
        # Status transitions and field changes
        if status_transitions:
            doc["status_transitions"] = status_transitions
        if field_changes:
            doc["field_changes"] = field_changes
        return doc, issue_data.get('issueId')  # Return both document and ID for ES indexing
