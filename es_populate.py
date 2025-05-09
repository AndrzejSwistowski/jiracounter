"""
Elasticsearch implementation for storing Jira changelog data.

This module provides functionality to store and retrieve Jira changelog data in Elasticsearch.
It replaces the SQL data warehouse implementation with Elasticsearch indices for better search 
and analysis capabilities.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from jiraservice import JiraService
from utils import APP_TIMEZONE, parse_date_with_timezone
import config
import dateutil.parser
from es_mapping import CHANGELOG_MAPPING, SETTINGS_MAPPING

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

# Get Elasticsearch settings from environment variables
# Format for ELASTIC_URL is expected to be: http://hostname:port/
ELASTIC_URL = os.environ.get('ELASTIC_URL')
ELASTIC_APIKEY = os.environ.get('ELASTIC_APIKEY')

# Default Elasticsearch connection settings if environment variables not set
ES_HOST = "localhost"
ES_PORT = 9200
ES_USE_SSL = False

# If ELASTIC_URL is provided, parse it to extract host, port, and protocol
if ELASTIC_URL:
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(ELASTIC_URL)
        ES_HOST = parsed_url.hostname or ES_HOST
        ES_PORT = parsed_url.port or ES_PORT
        ES_USE_SSL = parsed_url.scheme == 'https'
        logger.info(f"Using Elasticsearch URL from environment: {ELASTIC_URL}")
    except Exception as e:
        logger.warning(f"Error parsing ELASTIC_URL: {e}. Using defaults.")

# Index names
INDEX_CHANGELOG = "jira-changelog"
INDEX_SETTINGS = "jira-settings"

class JiraElasticsearchPopulator:
    """
    Handles populating Elasticsearch with data from the JIRA API.
    Connects to Elasticsearch and manages the indices for storing JIRA data.
    """
    
    def __init__(self, agent_name="JiraETLAgent", host=ES_HOST, port=ES_PORT,
                 api_key=ELASTIC_APIKEY, use_ssl=ES_USE_SSL, url=ELASTIC_URL):
        """
        Initialize the Elasticsearch populator.
        
        Args:
            agent_name: Identifier for this ETL agent in the settings index
            host: Elasticsearch host
            port: Elasticsearch port
            api_key: Elasticsearch API key (optional)
            use_ssl: Whether to use SSL for Elasticsearch connection
            url: Full Elasticsearch URL (will override host/port if provided)
        """
        self.agent_name = agent_name
        self.jira_service = JiraService()
        self.es = None
        self.host = host
        self.port = port
        self.api_key = api_key
        self.use_ssl = use_ssl
        self.url = url
        
    def connect(self):
        """Establishes a connection to Elasticsearch."""
        try:
            # Remove trailing slash if present in URL
            if self.url:
                self.url = self.url.rstrip('/')
            
            # First, test the connection using requests library (which we know works)
            import requests
            
            # Build base URL
            if self.url:
                base_url = self.url
            else:
                base_url = f'{"https" if self.use_ssl else "http"}://{self.host}:{self.port}'
                
            # Prepare headers with API key authentication
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"ApiKey {self.api_key}"
                logger.info("Using API key authentication")
            
            # Test the connection by requesting cluster health
            response = requests.get(f"{base_url}/_cluster/health", headers=headers)
            
            if response.status_code != 200:
                raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code} - {response.text}")
                
            health_data = response.json()
            logger.info(f"Successfully connected to Elasticsearch cluster: {health_data['cluster_name']} / Status: {health_data['status']}")
            
            # Now, create the Elasticsearch client instance with the same connection params
            connect_args = {'hosts': [base_url]}
            
            # Add API key authentication if provided - using headers like in requests
            if self.api_key:
                connect_args['headers'] = headers
            
            self.es = Elasticsearch(**connect_args)
            
            # We won't check with ping() since we already verified the connection works
            
            return self.es
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {e}")
            raise
    
    def close(self):
        """Closes the Elasticsearch connection."""
        if self.es:
            self.es.close()
            logger.info("Elasticsearch connection closed")
    
    def create_indices(self):
        """Create the necessary indices with proper mappings."""
        try:
            # Create changelog index with the improved mapping
            self.es.indices.create(
                index=INDEX_CHANGELOG,
                body=CHANGELOG_MAPPING,
                ignore=400  # Ignore error if index already exists
            )
            
            # Create settings index
            self.es.indices.create(
                index=INDEX_SETTINGS,
                body=SETTINGS_MAPPING,
                ignore=400  # Ignore error if index already exists
            )
            
            return True
        except Exception as e:
            logging.error(f"Error creating indices: {e}")
            return False
    
    def get_last_sync_date(self):
        """
        Gets the last date when data was fetched from JIRA API.
        
        Returns:
            datetime: The date of the last sync, or None if no previous sync
        """
        try:
            # Make sure indices exist
            self.create_indices()
            
            # Query for the agent's settings
            query = {
                "query": {
                    "term": {
                        "agent_name": self.agent_name
                    }
                }
            }
            
            result = self.es.search(index=INDEX_SETTINGS, body=query)
            
            if result["hits"]["total"]["value"] > 0:
                # Return the last_sync_date value
                return datetime.fromisoformat(result["hits"]["hits"][0]["_source"]["last_sync_date"]).astimezone(APP_TIMEZONE)
            else:
                # If no parameters found, try to get the last imported issue date
                query = {
                    "size": 1,
                    "sort": [
                        {
                            "historyDate": {
                                "order": "desc"
                            }
                        }
                    ]
                }
                
                result = self.es.search(index=INDEX_CHANGELOG, body=query)
                
                if result["hits"]["total"]["value"] > 0:
                    return datetime.fromisoformat(result["hits"]["hits"][0]["_source"]["historyDate"]).astimezone(APP_TIMEZONE)
                
                # If still no date, return None
                return None
                
        except Exception as e:
            logger.error(f"Error getting last sync date: {e}")
            return None
    
    def update_sync_date(self, sync_date):
        """
        Updates the last sync date in Elasticsearch.
        
        Args:
            sync_date: The datetime to save as the last sync date
        """
        try:
            # Make sure indices exist
            self.create_indices()
            
            # Prepare the document
            doc = {
                "agent_name": self.agent_name,
                "last_sync_date": sync_date.isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Query to check if the document exists
            query = {
                "query": {
                    "term": {
                        "agent_name": self.agent_name
                    }
                }
            }
            
            result = self.es.search(index=INDEX_SETTINGS, body=query)
            
            if result["hits"]["total"]["value"] > 0:
                # Update the existing document
                doc_id = result["hits"]["hits"][0]["_id"]
                self.es.update(index=INDEX_SETTINGS, id=doc_id, body={"doc": doc})
            else:
                # Insert a new document
                self.es.index(index=INDEX_SETTINGS, body=doc)
            
            logger.info(f"Updated last sync date to {sync_date}")
        except Exception as e:
            logger.error(f"Error updating sync date: {e}")
    
    def format_changelog_entry(self, history_record):
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
                "name": self._get_allocation_name(history_record['allocationCode'])
            }
        
        if history_record.get('parentKey'):
            doc["parentKey"] = history_record['parentKey']
        
        # Add changes if available
        if history_record.get('changes'):
            doc["changes"] = history_record['changes']
        
        return doc
    
    def _get_allocation_name(self, code):
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
    
    def insert_issue_history(self, history_record):
        """
        Inserts an issue history record into Elasticsearch.
        
        Args:
            history_record: Dictionary containing the issue history data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Make sure indices exist
            self.create_indices()
            
            # Format the record for Elasticsearch
            doc = self.format_changelog_entry(history_record)
            
            # Check if this record already exists
            query = {
                "query": {
                    "term": {
                        "historyId": history_record['historyId']
                    }
                }
            }
            
            result = self.es.search(index=INDEX_CHANGELOG, body=query)
            
            if result["hits"]["total"]["value"] > 0:
                logger.debug(f"Record with historyId {history_record['historyId']} already exists, skipping")
                return True
                
            # Insert the record
            self.es.index(index=INDEX_CHANGELOG, body=doc)
            logger.debug(f"Inserted history record for {history_record['issueKey']} with ID {history_record['historyId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting issue history: {e}")
            return False
    
    def bulk_insert_issue_history(self, history_records):
        """
        Inserts multiple issue history records into Elasticsearch in a single bulk operation.
        
        Args:
            history_records: List of dictionaries containing issue history data
            
        Returns:
            int: Number of records successfully inserted
        """
        try:
            if not history_records:
                return 0
                
            # Make sure indices exist
            self.create_indices()
            
            # Prepare the bulk operation
            actions = []
            for record in history_records:
                # Check if this record already exists
                query = {
                    "query": {
                        "term": {
                            "historyId": record['historyId']
                        }
                    }
                }
                
                result = self.es.search(index=INDEX_CHANGELOG, body=query)
                
                if result["hits"]["total"]["value"] > 0:
                    logger.info(f"Record with historyId {record['historyId']} already exists, skipping")
                    continue
                
                # Format the record for Elasticsearch
                doc = self.format_changelog_entry(record)
                
                # Add the action
                actions.append({
                    "_index": INDEX_CHANGELOG,
                    "_source": doc,
                    # Add a metadata ID to help with error tracking
                    "_id": f"{record['issueKey']}_{record['historyId']}"
                })
            
            # Execute the bulk operation
            if actions:
                try:
                    success, errors = bulk(self.es, actions, stats_only=False, raise_on_error=False)
                    
                    if errors:
                        # Log detailed error information for failed documents
                        for error_item in errors:
                            op_type = list(error_item.keys())[0]
                            error_info = error_item[op_type]
                            
                            error_reason = "Unknown error"
                            error_doc_id = "Unknown"
                            
                            # Extract error details
                            if 'error' in error_info:
                                if isinstance(error_info['error'], dict):
                                    error_reason = error_info['error'].get('reason', 'Unknown reason')
                                    error_type = error_info['error'].get('type', 'Unknown type')
                                    error_reason = f"{error_type}: {error_reason}"
                                else:
                                    error_reason = str(error_info['error'])
                                    
                            if '_id' in error_info:
                                error_doc_id = error_info['_id']
                                
                            logger.error(f"Failed to index document with ID {error_doc_id}: {error_reason}")
                            
                            # Try to find and log the problematic document
                            for action in actions:
                                if action.get('_id') == error_doc_id:
                                    # Log a sanitized version of the document for debugging
                                    logger.debug(f"Problematic document content (partial): issue={action.get('_source', {}).get('issue', {})}")
                                    break
                        
                        logger.warning(f"Bulk insert: {success} succeeded, {len(errors)} failed")
                    else:
                        logger.debug(f"Bulk insert: {success} succeeded, 0 failed")
                    
                    return success
                except Exception as e:
                    logger.error(f"Error during bulk operation: {e}")
                    
                    # Fall back to individual inserts with better error handling
                    logger.info("Falling back to individual document inserts")
                    success_count = 0
                    
                    for action in actions:
                        try:
                            self.es.index(
                                index=action['_index'],
                                id=action.get('_id'),
                                body=action['_source']
                            )
                            success_count += 1
                        except Exception as doc_error:
                            logger.error(f"Failed to index document {action.get('_id')}: {doc_error}")
                    
                    logger.info(f"Individual insert fallback: {success_count} succeeded, {len(actions) - success_count} failed")
                    return success_count
            else:
                logger.debug("No new records to insert")
                return 0
                
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            return 0
    
    def populate_from_jira(self, start_date=None, end_date=None, max_issues=None, bulk_size=100):
        """
        Fetches data from JIRA and populates Elasticsearch.
        
        Args:
            start_date: The date to start fetching from (default: last sync date)
            end_date: The date to fetch up to (default: now)
            max_issues: Maximum number of issues to process (default: no limit)
            bulk_size: Number of records to insert in each bulk operation
            
        Returns:
            int: Number of records successfully inserted
        """
        if not self.es:
            self.connect()
        
        # If no start_date provided, get the last sync date
        if not start_date:
            start_date = self.get_last_sync_date()
        
        # If no end_date provided, use current time in UTC
        if not end_date:
            end_date = datetime.now(APP_TIMEZONE)
            
        logger.info(f"Populating Elasticsearch with JIRA data from {start_date} to {end_date}")
        
        # Flag to track if we successfully connected to JIRA
        jira_connected = False
        success_count = 0
        
        try:
            # Get issue history records from JIRA
            result = self.jira_service.get_issue_history(start_date=start_date, end_date=end_date, max_issues=max_issues)
            if result is None:
                history_records = []
            else:
                history_records = result
					
            # If we get here, JIRA authentication was successful
            jira_connected = True
            
            # Process records in bulk
            bulk_data = []
            current_bulk_size = 0
            total_inserted = 0
            
            for record in history_records:
                # Transform the record to Elasticsearch format
                es_record = self.transform_record_for_elasticsearch(record)
                
                # Add to bulk operation
                bulk_data.append({
                    "index": {
                        "_index": INDEX_CHANGELOG,
                        "_id": str(es_record['historyId'])
                    }
                })
                bulk_data.append(es_record)
                current_bulk_size += 1
                
                # Process the bulk when it reaches the desired size
                if current_bulk_size >= bulk_size:
                    success, failed = self._execute_bulk(bulk_data)
                    total_inserted += success
                    bulk_data = []
                    current_bulk_size = 0
            
            # Process any remaining records
            if bulk_data:
                success, failed = self._execute_bulk(bulk_data)
                total_inserted += success
            
            logger.info(f"Successfully inserted {total_inserted} out of {len(history_records)} records")
            
        except Exception as e:
            logger.error(f"Error fetching data from JIRA: {e}")
            # Note: We'll still update the sync date below if jira_connected is True
        
        # Update the last sync date if we successfully connected to JIRA,
        # even if we couldn't insert all records or encountered other errors
        if jira_connected:
            try:
                self.update_sync_date(end_date)
                logger.info(f"Updated last sync date to {end_date}")
            except Exception as e:
                logger.error(f"Error updating sync date: {e}")
                
        else:
            logger.warning("JIRA authorization may have failed. Not updating the sync date.")
        
        return success_count
    
    def get_database_summary(self, days=30):
        """
        Gets a summary of the data in Elasticsearch.
        
        Args:
            days: Number of days to include in the summary (default: 30)
            
        Returns:
            dict: Summary statistics about the database
        """
        try:
            # Calculate the date range
            end_date = datetime.now(APP_TIMEZONE)
            start_date = end_date - timedelta(days=30)
            
            # Build the query
            query = {
                "query": {
                    "range": {
                        "historyDate": {
                            "gte": start_date.isoformat(),
                            "lte": end_date.isoformat()
                        }
                    }
                },
                "aggs": {
                    "total_records": {
                        "value_count": {
                            "field": "historyId"
                        }
                    },
                    "oldest_record": {
                        "min": {
                            "field": "historyDate"
                        }
                    },
                    "newest_record": {
                        "max": {
                            "field": "historyDate"
                        }
                    },
                    "unique_issues": {
                        "cardinality": {
                            "field": "issue.id"
                        }
                    },
                    "unique_projects": {
                        "cardinality": {
                            "field": "project.key"
                        }
                    }
                },
                "size": 0  # We don't need the actual documents, just the aggregations
            }
            
            # Execute the query
            result = self.es.search(index=INDEX_CHANGELOG, body=query)
            
            # Extract the results
            aggs = result.get('aggregations', {})
            
            return {
                'total_records': aggs.get('total_records', {}).get('value', 0),
                'oldest_record': aggs.get('oldest_record', {}).get('value_as_string'),
                'newest_record': aggs.get('newest_record', {}).get('value_as_string'),
                'unique_issues': aggs.get('unique_issues', {}).get('value', 0),
                'unique_projects': aggs.get('unique_projects', {}).get('value', 0)
            }
                
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return None

    def update_field_mapping(self):
        """
        Updates the field mapping in an existing index to enable fielddata for text fields used in aggregations.
        This allows aggregations on fields that were previously not configured for it.
        """
        try:
            # Use the requests library which we know works with your setup
            import requests
            
            # Build base URL
            if self.url:
                base_url = self.url.rstrip('/')
            else:
                base_url = f'{"https" if self.use_ssl else "http"}://{self.host}:{self.port}'
                
            # Prepare headers with API key authentication
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"ApiKey {self.api_key}"
            
            # Update mapping to enable fielddata on issue.id field and other fields used in aggregations
            mapping_update = {
                "properties": {
                    "issue": {
                        "properties": {
                            "id": {
                                "type": "text",
                                "fielddata": True
                            }
                        }
                    },
                    "project": {
                        "properties": {
                            "key": {
                                "type": "text",
                                "fielddata": True
                            }
                        }
                    }
                }
            }
            
            # Apply the mapping update
            update_response = requests.put(
                f"{base_url}/{INDEX_CHANGELOG}/_mapping",
                headers=headers,
                json=mapping_update
            )
            
            if update_response.status_code >= 200 and update_response.status_code < 300:
                logger.info(f"Successfully updated mapping for {INDEX_CHANGELOG} index")
                return True
            else:
                error_detail = update_response.text
                logger.error(f"Error updating mapping: {update_response.status_code} - {error_detail}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating field mapping: {e}")
            return False

    def prepare_changelog_document(self, issue_key, history):
        """Prepare a document for the changelog index, with improved searchability."""
        # Get issue summary from Jira if needed
        issue_summary = ""
        try:
            # Try to get summary from Jira service if needed
            issue_data = self.jira_service.get_issue(issue_key)
            if issue_data and 'fields' in issue_data and 'summary' in issue_data['fields']:
                issue_summary = issue_data['fields']['summary']
        except Exception as e:
            logger.warning(f"Could not get summary for issue {issue_key}: {e}")
        
        # Calculate working days if possible
        working_days = None
        try:
            # Calculate working days between creation and the history date
            issue_data = self.jira_service.get_issue(issue_key)
            if issue_data and 'fields' in issue_data and 'created' in issue_data['fields']:
                created_date = parse_date_with_timezone(issue_data['fields']['created'])
                history_date = parse_date_with_timezone(history["created"])
                
                # Simple calculation (excluding weekends)
                delta = history_date - created_date
                working_days = max(0, delta.days - (delta.days // 7) * 2)
                
                # If created_date is on weekend, adjust accordingly
                created_weekday = created_date.weekday()
                if created_weekday > 4:  # 5=Saturday, 6=Sunday
                    working_days -= (6 - created_weekday)
        except Exception as e:
            logger.warning(f"Could not calculate working days for issue {issue_key}: {e}")
            
        doc = {
            "historyId": history["id"],
            "historyDate": history["created"],
            "@timestamp": history["created"],
            "issueKey": issue_key,
            "factType": "HISTORY"
        }
        
        # Add summary if available
        if issue_summary:
            doc["summary"] = issue_summary
            
        # Add working days if calculated
        if working_days is not None:
            doc["workingDaysFromCreation"] = working_days
            
        # Extract specific fields for better searchability
        description_text = ""
        comment_text = ""
        status_change = ""
        assignee_change = ""
        
        # Process each change item
        for item in history.get("items", []):
            change = {
                "field": item.get("field"),
                "fieldtype": item.get("fieldtype"),
                "from": item.get("from"),
                "fromString": item.get("fromString"),
                "to": item.get("to"),
                "toString": item.get("toString")
            }
            
            # Add to changes list
            doc.setdefault("changes", []).append(change)
            
            # Extract specific fields for better searchability
            if item.get("field") == "description":
                description_text = item.get("toString", "")
            elif item.get("field") == "comment":
                comment_text = item.get("toString", "")
            elif item.get("field") == "status":
                status_change = f"{item.get('fromString', '')} → {item.get('toString', '')}"
            elif item.get("field") == "assignee":
                assignee_change = f"{item.get('fromString', '')} → {item.get('toString', '')}"
            
        # Add extracted fields for better searchability
        if description_text:
            doc["description_text"] = description_text
        if comment_text:
            doc["comment_text"] = comment_text
        if status_change:
            doc["status_changes"] = status_change
        if assignee_change:
            doc["assignee_changes"] = assignee_change
            
        return doc

    def transform_record_for_elasticsearch(self, record):
        """Transform a JIRA record to the format needed for Elasticsearch."""
        es_record = record.copy()  # Start with a copy of the original record
        
        # Add timestamp field for Elasticsearch
        es_record['@timestamp'] = es_record.get('historyDate')
        
        # Process description_text field - ensure it's properly set
        if 'description_text' not in es_record or not es_record['description_text']:
            # Check changes collection for description
            if 'changes' in es_record:
                for change in es_record['changes']:
                    if change.get('field') == 'description' and change.get('to'):
                        es_record['description_text'] = change.get('to')
                        break
        
        # Process comment_text field
        # Keep as is, already set by the JiraService
        
        # Process status change information
        if 'changes' in es_record:
            status_changes = []
            for change in es_record['changes']:
                if change.get('field') == 'status':
                    status_from = change.get('from', '')
                    status_to = change.get('to', '')
                    status_changes.append(f"{status_from} → {status_to}")
            
            if status_changes:
                es_record['status_change'] = status_changes
        
        # Process assignee change information
        if 'changes' in es_record:
            assignee_changes = []
            for change in es_record['changes']:
                if change.get('field') == 'assignee':
                    assignee_from = change.get('from', '')
                    assignee_to = change.get('to', '')
                    assignee_changes.append(f"{assignee_from} → {assignee_to}")
            
            if assignee_changes:
                es_record['assignee_change'] = assignee_changes
        
        # Ensure date fields are properly formatted
        for date_field in ['status_change_date', 'created', 'updated']:
            if date_field in es_record and es_record[date_field]:
                # Make sure it's properly formatted as ISO8601
                try:
                    if not isinstance(es_record[date_field], str):
                        # Convert datetime object to string if needed
                        es_record[date_field] = es_record[date_field].isoformat()
                except:
                    pass  # Keep as is if conversion fails
        
        return es_record

    def _execute_bulk(self, actions):
        # Method implementation
        pass
            
# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("jira_etl_es.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create and use the populator
    populator = JiraElasticsearchPopulator()
    try:
        populator.connect()
        
        # Populate with the last 7 days of data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        count = populator.populate_from_jira(start_date, end_date)
        print(f"Inserted {count} records")
        
        # Get and print a summary
        summary = populator.get_database_summary()
        if summary:
            print(f"Elasticsearch Summary:")
            print(f"Total Records: {summary['total_records']}")
            print(f"Date Range: {summary['oldest_record']} to {summary['newest_record']}")
            print(f"Unique Issues: {summary['unique_issues']}")
            print(f"Unique Projects: {summary['unique_projects']}")
            
    finally:
        populator.close()