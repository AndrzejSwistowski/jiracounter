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
        # Import time_utils functions for period formatting
        from time_utils import format_working_minutes_to_text
        
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
                    "change_at": history_record.get('status_change_date'),
                    "working_minutes": history_record.get('working_minutes_in_status'),
                    "working_days": int(history_record['working_minutes_in_status'] / (60 * 8)) if history_record.get('working_minutes_in_status') else None,
                    "period": format_working_minutes_to_text(history_record.get('working_minutes_in_status'))
                },
                "created_at": history_record.get('created'),
                "working_minutes": history_record.get('working_minutes_from_create'),
                "working_days": int(history_record['working_minutes_from_create'] / (60 * 8)) if history_record.get('working_minutes_from_create') else None,
                "period": format_working_minutes_to_text(history_record.get('working_minutes_from_create'))
            },
            "project": {
                "key": history_record['projectKey'],
            }    
        }
        
        # Add allocation field (as keyword according to mapping)
        if history_record.get('allocationCode'):
            doc["allocation"] = history_record['allocationCode']

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

        # Add summary field with text analysis according to mapping
        if history_record.get('summary'):
            doc["summary"] = history_record['summary']
            
            
            
        # Add parent_issue with proper structure according to mapping
        if history_record.get('parent_issue'):
            doc["parent_issue"] = {
                "key": history_record.get('parentKey') or history_record['parent_issue'].get('key'),
                "summary": history_record.get('parent_summary') or history_record['parent_issue'].get('summary')
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
                "displayName": history_record['reporterDisplayName']            }
            
        # Add assignee with proper structure according to mapping
        if history_record.get('assigneeDisplayName'):
            doc["assignee"] = {
                "displayName": history_record['assigneeDisplayName']
            }

        if history_record.get('authorDisplayName'):
            doc["author"] = {
                "displayName": history_record['authorDisplayName']
            }

        # Add changes as nested objects according to mapping
        if history_record.get('changes'):
            doc["changes"] = history_record['changes']
        
        # Add content text fields with comprehensive text analysis
        if history_record.get('description_text'):
            doc["description"] = history_record['description_text']
            
        if history_record.get('comment_text'):
            doc["comment"] = history_record['comment_text']


        if history_record.get('todo_exit_date') is not None:
            doc["selected_for_development_at"] = history_record['todo_exit_date']
            
        # Add categorized time metrics as nested objects according to mapping
        if history_record.get('backlog_minutes') is not None:
            doc["backlog"] = {
                "working_minutes": history_record['backlog_minutes'],
                "working_days": int(history_record['backlog_minutes'] / (60 * 8)),
                "period": format_working_minutes_to_text(history_record['backlog_minutes'])
            }

        
        if history_record.get('processing_minutes') is not None:
            doc["processing"] = {
                "working_minutes": history_record['processing_minutes'],
                "working_days": int(history_record['processing_minutes'] / (60 * 8)),
                "period": format_working_minutes_to_text(history_record['processing_minutes'])
            }

        if history_record.get('waiting_minutes') is not None:
            doc["waiting"] = {
                "working_minutes": history_record['waiting_minutes'],
                "working_days": int(history_record['waiting_minutes'] / (60 * 8)),
                "period": format_working_minutes_to_text(history_record['waiting_minutes'])
            }

        if history_record.get('working_minutes_from_move_at_point') is not None:
            doc["from_selected_for_development"] = {
                "working_minutes": history_record['working_minutes_from_move_at_point'],
                "working_days": int(history_record['working_minutes_from_move_at_point'] / (60 * 8)),
                "period": format_working_minutes_to_text(history_record['working_minutes_from_move_at_point'])
            }

        # Add status transition metrics
        if history_record.get('total_transitions') is not None:
            doc["total_transitions"] = history_record['total_transitions']
            
        if history_record.get('backflow_count') is not None:
            doc["backflow_count"] = history_record['backflow_count']
            
        if history_record.get('unique_statuses_visited'):
            doc["unique_statuses_visited"] = history_record['unique_statuses_visited']
            
        # Store only the last status transition instead of the entire collection
        if history_record.get('status_transitions') and len(history_record['status_transitions']) > 0:
            last_transition = history_record['status_transitions'][-1]  # Get the last transition
            doc["status_transitions"] = last_transition

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
    
    @staticmethod
    def format_comprehensive_record(comprehensive_record):
        """
        Format a comprehensive issue record for insertion into Elasticsearch.
        
        This method handles the new comprehensive record structure that contains
        all issue data, metrics, and history in a single record per issue.
        
        Args:
            comprehensive_record: Dictionary containing the comprehensive issue data
                                 with keys: issue_data, issue_description, issue_comments,
                                 metrics, status_transitions, field_changes
            
        Returns:
            Dict containing the formatted data for Elasticsearch
        """
        from time_utils import format_working_minutes_to_text
        
        # Extract main components from the comprehensive record
        issue_data = comprehensive_record.get('issue_data', {})
        metrics = comprehensive_record.get('metrics', {})
        status_transitions = comprehensive_record.get('status_transitions', [])
        field_changes = comprehensive_record.get('field_changes', [])
        
        # Create the base document structure
        doc = {
            # Use the issue key and current timestamp as identifiers
            "historyId": f"{issue_data.get('key', 'unknown')}_comprehensive",
            "historyDate": issue_data.get('updated'),
            "@timestamp": issue_data.get('updated'),
            "factType": "COMPREHENSIVE_ISSUE",
            "issue": {
                "key": issue_data.get('key'),
                "type": {
                    "name": issue_data.get('typeName')
                },
                "status": {
                    "name": issue_data.get('statusName'),
                    "change_at": metrics.get('current_status_since'),
                    "working_minutes": metrics.get('working_minutes_in_current_status'),
                    "working_days": int(metrics.get('working_minutes_in_current_status', 0) / (60 * 8)) if metrics.get('working_minutes_in_current_status') else None,
                    "period": format_working_minutes_to_text(metrics.get('working_minutes_in_current_status'))
                },
                "created_at": issue_data.get('created'),
                "working_minutes": metrics.get('total_working_minutes'),
                "working_days": int(metrics.get('total_working_minutes', 0) / (60 * 8)) if metrics.get('total_working_minutes') else None,
                "period": format_working_minutes_to_text(metrics.get('total_working_minutes'))
            },
            "project": {
                "key": issue_data.get('projectKey'),
            }    
        }
        
        # Add allocation field
        if issue_data.get('allocationCode'):
            doc["allocation"] = issue_data['allocationCode']

        # Add labels as keyword array
        if issue_data.get('labels'):
            doc["labels"] = issue_data['labels']
        
        # Add components
        if issue_data.get('components'):
            component_names = ElasticsearchDocumentFormatter._extract_component_names(
                issue_data.get('components'), 
                issue_data.get('key')
            )
            if component_names:
                doc["components"] = component_names

        # Add summary field
        if issue_data.get('summary'):
            doc["summary"] = issue_data['summary']
            
        # Add parent_issue with proper structure
        if issue_data.get('parent_issue'):
            doc["parent_issue"] = {
                "key": issue_data.get('parentKey') or issue_data['parent_issue'].get('key'),
                "summary": issue_data.get('parent_summary') or issue_data['parent_issue'].get('summary')
            }
            
        # Add epic_issue with proper structure
        if issue_data.get('epic_issue'):
            doc["epic_issue"] = {
                "key": issue_data['epic_issue'].get('key'),
                "summary": issue_data['epic_issue'].get('summary')
            }
        
        # Add reporter
        if issue_data.get('reporterDisplayName'):
            doc["reporter"] = {
                "displayName": issue_data['reporterDisplayName']
            }
            
        # Add assignee
        if issue_data.get('assigneeDisplayName'):
            doc["assignee"] = {
                "displayName": issue_data['assigneeDisplayName']
            }

        # Add content text fields
        if comprehensive_record.get('issue_description'):
            doc["description"] = comprehensive_record['issue_description']
            
        # Process comments - convert array to concatenated text for ES indexing
        if comprehensive_record.get('issue_comments'):
            comments = comprehensive_record['issue_comments']
            if isinstance(comments, list) and comments:
                # Concatenate all comment bodies for full-text search
                comment_texts = []
                for comment in comments:
                    if isinstance(comment, dict) and comment.get('body'):
                        comment_texts.append(comment['body'])
                    elif isinstance(comment, str):
                        comment_texts.append(comment)
                
                if comment_texts:
                    doc["comment"] = " ".join(comment_texts)

        # Add categorized time metrics from the metrics section
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

        # Add development selection date if available
        if metrics.get('todo_exit_date') is not None:
            doc["selected_for_development_at"] = metrics['todo_exit_date']
            
        # Add working minutes from development selection point
        if metrics.get('working_minutes_from_todo_exit') is not None:
            doc["from_selected_for_development"] = {
                "working_minutes": metrics['working_minutes_from_todo_exit'],
                "working_days": int(metrics['working_minutes_from_todo_exit'] / (60 * 8)),
                "period": format_working_minutes_to_text(metrics['working_minutes_from_todo_exit'])
            }

        # Add status transition metrics
        if metrics.get('total_transitions') is not None:
            doc["total_transitions"] = metrics['total_transitions']
            
        if metrics.get('backflow_count') is not None:
            doc["backflow_count"] = metrics['backflow_count']
            
        if metrics.get('unique_statuses_visited'):
            doc["unique_statuses_visited"] = metrics['unique_statuses_visited']
            
        # Store the most recent status transition
        if status_transitions and len(status_transitions) > 0:
            last_transition = status_transitions[-1]  # Get the last transition
            doc["status_transitions"] = last_transition

        # Store field changes as nested objects for analysis
        if field_changes:
            doc["changes"] = field_changes

        return doc
