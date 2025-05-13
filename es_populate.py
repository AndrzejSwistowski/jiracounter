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
from es_document_formatter import ElasticsearchDocumentFormatter

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
if (ELASTIC_URL):
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
        return ElasticsearchDocumentFormatter.format_changelog_entry(history_record)
    
    # Remove the _get_allocation_name method as it's already handled by ElasticsearchDocumentFormatter
    
    def insert_issue_history(self, history_record):
        """
        Inserts an issue history record into Elasticsearch.
        
        This method is deprecated and will be removed in the future.
        Use bulk_insert_issue_history instead for better performance.
        
        Args:
            history_record: Dictionary containing the issue history data
            
        Returns:
            bool: True if successful, False otherwise
        """
        import warnings
        warnings.warn(
            "insert_issue_history is deprecated. Use bulk_insert_issue_history instead.", 
            DeprecationWarning, 
            stacklevel=2
        )
        
        # Call bulk_insert_issue_history with a single record
        result = self.bulk_insert_issue_history([history_record])
        return result > 0
    
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
                try:
                    # Check if historyId exists and is valid
                    if 'historyId' not in record:
                        logger.warning(f"Record missing historyId, skipping: {record.get('issueKey', 'unknown')}")
                        continue
                        
                    # Format the record for Elasticsearch
                    doc = self.format_changelog_entry(record)
                    
                    # Generate a unique ID for the document
                    doc_id = f"{record.get('issueKey', 'unknown')}_{record['historyId']}"
                    
                    # Add the action
                    actions.append({
                        "_index": INDEX_CHANGELOG,
                        "_id": doc_id,
                        "_source": doc
                    })
                except Exception as e:
                    logger.error(f"Error processing record: {e}")
                    logger.debug(f"Problematic record: {record.get('historyId', 'unknown')} for issue {record.get('issueKey', 'unknown')}")
                    continue
            
            # Execute the bulk operation
            if actions:
                try:
                    success_count = 0
                    failed_count = 0
                    
                    # Use the bulk helper from elasticsearch library
                    success, errors = bulk(self.es, actions, stats_only=True, raise_on_error=False)
                    
                    success_count = success
                    failed_count = len(actions) - success if success <= len(actions) else 0
                    
                    if failed_count > 0:
                        logger.warning(f"Bulk insert: {success_count} succeeded, {failed_count} failed")
                    else:
                        logger.debug(f"Bulk insert: {success_count} succeeded")
                    
                    return success_count
                except Exception as e:
                    logger.error(f"Error during bulk operation: {e}")
                    return 0
            else:
                logger.debug("No new records to insert")
                return 0
                
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            return 0

    def populate_from_jira(self, start_date=None, end_date=None, max_issues=None, bulk_size=100):
        """
        Fetches data from JIRA and populates Elasticsearch.
        
        IMPORTANT REQUIREMENT: 
        1. If any bulk operation fails, the function should save the last successfully 
           processed history date as the sync date (rather than the requested end_date).
        2. If no records were successfully processed, the function should exit without 
           updating the sync date.
        3. Early exit is required after a bulk operation failure to prevent further processing.
        
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
        # Flag to track if all bulk operations succeeded
        all_bulk_operations_succeeded = True
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
            current_bulk_idx = 0
            total_inserted = 0
            
            # Track the last successfully processed history date
            last_successful_date = None
            
            # Process records in batches
            for i in range(0, len(history_records), bulk_size):
                batch = history_records[i:i+bulk_size]
                inserted_count = self.bulk_insert_issue_history(batch)
                total_inserted += inserted_count
                
                # If nothing was inserted in this batch, there might be an issue
                if inserted_count == 0 and len(batch) > 0:
                    all_bulk_operations_succeeded = False
                    logger.warning(f"Batch insert failed - 0 records inserted out of {len(batch)}")
                    break
                
                # Update the last successful date if records were inserted
                if inserted_count > 0 and batch:
                    last_record = batch[-1]
                    if last_record.get('historyDate'):
                        try:
                            record_date = datetime.fromisoformat(last_record['historyDate']) if isinstance(last_record['historyDate'], str) else last_record['historyDate']
                            if isinstance(record_date, datetime):
                                last_successful_date = record_date
                        except (ValueError, TypeError):
                            logger.debug(f"Could not parse historyDate: {last_record.get('historyDate')}")
            
            logger.info(f"Successfully inserted {total_inserted} out of {len(history_records)} records")
            success_count = total_inserted
            
        except Exception as e:
            logger.error(f"Error fetching data from JIRA: {e}")
            all_bulk_operations_succeeded = False
        
        # Early exit if nothing was processed successfully
        if success_count == 0:
            logger.warning("No records were processed successfully. Exiting without updating sync date.")
            return 0
            
        # Determine what date to use for the sync
        if jira_connected:
            try:
                if all_bulk_operations_succeeded:
                    # Use the end_date if all operations succeeded
                    self.update_sync_date(end_date)
                    logger.info(f"Updated last sync date to {end_date}")
                else:
                    # Use the last successful history date if any operation failed
                    if last_successful_date:
                        self.update_sync_date(last_successful_date)
                        logger.info(f"Bulk operations had failures. Updated last sync date to last successful record date: {last_successful_date}")
                    else:
                        logger.warning("Could not determine last successful date. Not updating the sync date.")
            except Exception as e:
                logger.error(f"Error updating sync date: {e}")
        else:
            logger.warning("JIRA authorization failed. Not updating the sync date.")
        
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