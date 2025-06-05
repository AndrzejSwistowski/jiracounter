"""
Elasticsearch implementation for storing Jira changelog data.

This module provides functionality to store and retrieve Jira changelog data in Elasticsearch.
It replaces the SQL data warehouse implementation with Elasticsearch indices for better search 
and analysis capabilities.
"""

import json
import logging
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import requests

from config import ES_HOST, ES_PORT 
from es_document_formatter import ElasticsearchDocumentFormatter
from es_utils import create_index_with_auto_fallback
from jiraservice import JiraService
from logger_utils import setup_logging
from progress_tracker import ProgressTracker
from utils import APP_TIMEZONE, parse_date_with_timezone
import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

# Get Elasticsearch configuration from centralized config
ES_CONFIG = config.get_elasticsearch_config()
ELASTIC_URL = ES_CONFIG['url']
ELASTIC_APIKEY = ES_CONFIG['api_key']
ES_HOST = ES_CONFIG['host']
ES_PORT = ES_CONFIG['port']
ES_USE_SSL = ES_CONFIG['use_ssl']

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
        self.host = host
        self.port = port
        self.api_key = api_key
        self.use_ssl = use_ssl
        self.url = url
        self.connected = False
        self.base_url = None
        self.headers = None
   
    def connect(self):
        """Establishes a connection to Elasticsearch using HTTP requests."""
        try:
            # Remove trailing slash if present in URL
            if self.url:
                self.url = self.url.rstrip('/')
            
            # Build base URL
            if self.url:
                self.base_url = self.url
            else:
                self.base_url = f'{"https" if self.use_ssl else "http"}://{self.host}:{self.port}'
                
            # Prepare headers with API key authentication
            self.headers = {"Content-Type": "application/json"}
            if self.api_key:
                self.headers["Authorization"] = f"ApiKey {self.api_key}"
                logger.info("Using API key authentication")
            
            # Test the connection by requesting cluster health
            response = requests.get(f"{self.base_url}/_cluster/health", headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code} - {response.text}")
                
            health_data = response.json()
            logger.info(f"Successfully connected to Elasticsearch cluster: {health_data['cluster_name']} / Status: {health_data['status']}")
            
            # Store connection parameters for later use
            self.connected = True
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {e}")
            raise
    
    def close(self):
        """Closes the Elasticsearch connection."""
        if self.connected:
            self.connected = False
            logger.info("Elasticsearch connection closed")
    
    def create_indices(self):
        """Create the necessary indices with proper mappings using unified approach."""
        try:
            # Create changelog index using unified approach
            result1 = create_index_with_auto_fallback(
                populator=self,
                index_name=INDEX_CHANGELOG,
                logger=logger
            )
            
            # Create settings index using unified approach
            result2 = create_index_with_auto_fallback(
                populator=self,
                index_name=INDEX_SETTINGS,
                logger=logger
            )
            
            return result1 and result2        
        except Exception as e:

            logger.error(f"Error creating indices: {e}")
            return False

    def get_last_sync_date(self):
        """
        Gets the last date when data was fetched from JIRA API using HTTP requests.
        
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
            
            response = requests.post(f"{self.base_url}/{INDEX_SETTINGS}/_search", 
                                   headers=self.headers, json=query, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to query settings index: {response.status_code}")
                return None
                
            result = response.json()
            
            if result["hits"]["total"]["value"] > 0:
                # Return the last_sync_date value
                return datetime.fromisoformat(result["hits"]["hits"][0]["_source"]["last_sync_date"]).astimezone(APP_TIMEZONE)
            else:
                # If no parameters found, try to get the last imported issue date
                query = {
                    "size": 1,
                    "sort": [
                        {
                            "@timestamp": {
                                "order": "desc"
                            }
                        }
                    ]
                }
                
                response = requests.post(f"{self.base_url}/{INDEX_CHANGELOG}/_search", 
                                       headers=self.headers, json=query, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["hits"]["total"]["value"] > 0:
                        # Use the @timestamp field from the latest record
                        timestamp_str = result["hits"]["hits"][0]["_source"]["@timestamp"]
                        return datetime.fromisoformat(timestamp_str).astimezone(APP_TIMEZONE)
                
                # If still no date, return None
                return None
                
        except Exception as e:
            logger.error(f"Error getting last sync date: {e}")
            return None
    
    def update_sync_date(self, sync_date):
        """
        Updates the last sync date in Elasticsearch using HTTP requests.
        
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
            
            response = requests.post(f"{self.base_url}/{INDEX_SETTINGS}/_search", 
                                   headers=self.headers, json=query, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result["hits"]["total"]["value"] > 0:
                    # Update the existing document
                    doc_id = result["hits"]["hits"][0]["_id"]
                    update_body = {"doc": doc}
                    response = requests.post(f"{self.base_url}/{INDEX_SETTINGS}/_update/{doc_id}", 
                                           headers=self.headers, json=update_body, timeout=10)
                else:
                    # Insert a new document
                    response = requests.post(f"{self.base_url}/{INDEX_SETTINGS}/_doc", 
                                           headers=self.headers, json=doc, timeout=10)
                
                if response.status_code in [200, 201]:
                    logger.info(f"Updated last sync date to {sync_date}")
                else:
                    logger.error(f"Failed to update sync date: {response.status_code} - {response.text}")
            else:
                logger.error(f"Failed to query for existing settings: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error updating sync date: {e}")
    
    def format_changelog_entry(self, history_record):
        """
        Format a history record for insertion into Elasticsearch.
        
        This method is deprecated as it relies on the removed format_changelog_entry
        from ElasticsearchDocumentFormatter. Only comprehensive records are now supported.
        
        Args:
            history_record: Dictionary containing the issue history data
            
        Returns:
            Dict containing the formatted data for Elasticsearch
        """
        raise NotImplementedError("format_changelog_entry is no longer supported. Use comprehensive records only.")
    
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
        warnings.warn(
            "insert_issue_history is deprecated. Use bulk_insert_issue_history instead.", 
            DeprecationWarning, 
            stacklevel=2
        )        
        # Call bulk_insert_issue_history with a single record
        result = self.bulk_insert_issue_history([history_record])
        return result > 0
    
    def bulk_insert_issue_history(self, history_records, force_override=False):
        """
        Inserts multiple issue history records into Elasticsearch using HTTP bulk operations.
        
        Args:
            history_records: List of dictionaries containing comprehensive issue records
            force_override: If False (default), skip duplicates. If True, override existing records.
            
        Returns:
            int: Number of records successfully inserted
        """
        try:
            if not history_records:
                return 0
                  # Make sure indices exist
            self.create_indices()
            
            # Prepare the bulk operation
            bulk_body = []
            skipped_count = 0
            for record in history_records:
                try:
                    # All records are now issue records
                    doc, doc_id = self.format_issue_record(record)
                    # Use the actual issue ID returned by the formatter
                    if not doc_id:
                        # If no doc_id is found, raise an exception - we need a proper ID
                        issue_key = record.get('issue_data', {}).get('key', 'unknown')
                        raise ValueError(f"No document ID found for issue {issue_key}. Format_issue_record must return a valid ID.")
                    
                    # Check for duplicates if force_override is False
                    if not force_override:
                        # Extract @timestamp from the document for duplicate checking
                        timestamp = doc.get('@timestamp')
                        if timestamp and self.document_exists_by_id_and_timestamp(doc_id, timestamp):
                            skipped_count += 1
                            issue_key = record.get('issue_data', {}).get('key', 'unknown')
                            logger.debug(f"Skipping duplicate record for issue {issue_key} with timestamp {timestamp}")
                            continue
                    
                    # Add the index action
                    bulk_body.append(json.dumps({"index": {"_index": INDEX_CHANGELOG, "_id": doc_id}}))
                    bulk_body.append(json.dumps(doc))
                    
                except Exception as e:
                    logger.error(f"Error processing record: {e}")
                    issue_id = self._extract_issue_identifier(record)
                    logger.debug(f"Problematic record: {issue_id}")
                    continue            # Execute the bulk operation
            if bulk_body:
                try:
                    bulk_data = "\n".join(bulk_body) + "\n"
                    response = requests.post(f"{self.base_url}/_bulk", 
                                           headers=self.headers, 
                                           data=bulk_data, 
                                           timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        success_count = 0
                        failed_count = 0
                        
                        for item in result.get('items', []):
                            if 'index' in item:
                                if item['index'].get('status') in [200, 201]:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    logger.error(f"Bulk error: {item['index']}")
                        
                        if failed_count > 0:
                            if skipped_count > 0:
                                logger.warning(f"Bulk insert: {success_count} succeeded, {failed_count} failed, {skipped_count} duplicates skipped")
                            else:
                                logger.warning(f"Bulk insert: {success_count} succeeded, {failed_count} failed")
                        else:
                            if skipped_count > 0:
                                logger.info(f"Bulk insert: {success_count} succeeded, {skipped_count} duplicates skipped")
                            else:
                                logger.debug(f"Bulk insert: {success_count} succeeded")
                        
                        return success_count
                    else:
                        logger.error(f"Bulk operation failed: {response.status_code} - {response.text}")
                        return 0
                        
                except Exception as e:
                    logger.error(f"Error during bulk operation: {e}")
                    return 0
            else:
                if skipped_count > 0:
                    logger.info(f"No new records to insert. {skipped_count} duplicates were skipped")
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
        1. Always save the last successfully processed record date as the sync date,
           since we cannot guarantee that all records were fetched from JIRA due to 
           pagination limits, API limits, timeouts, etc.
        2. Only use the requested end_date if no records were processed but the operation
           succeeded (indicating the date range had no data).
        3. If no records were successfully processed, exit without updating the sync date.
        4. Early exit is required after a bulk operation failure to prevent further processing.
        
        Args:
            start_date: The date to start fetching from (default: last sync date)
            end_date: The date to fetch up to (default: now)
            max_issues: Maximum number of issues to process (default: no limit)
            bulk_size: Number of records to insert in each bulk operation
            
        Returns:
            int: Number of records successfully inserted        """
        if not self.connected:
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
            
            # Track the last successfully processed history date
            last_successful_date = None
            
            # Process records in batches
            for i in range(0, len(history_records), bulk_size):
                batch = history_records[i:i+bulk_size]
                inserted_count = self.bulk_insert_issue_history(batch)
                success_count += inserted_count
                
                # If nothing was inserted in this batch, there might be an issue
                if inserted_count == 0 and len(batch) > 0:
                    all_bulk_operations_succeeded = False
                    logger.warning(f"Batch insert failed - 0 records inserted out of {len(batch)}")
                    break
                
                # Update the last successful date if records were inserted
                if inserted_count > 0 and batch:
                    last_record = batch[-1]
                    # For the new comprehensive record structure, use issue_data.updated as the tracking date
                    if last_record.get('issue_data', {}).get('updated'):
                        try:
                            record_date = last_record['issue_data']['updated']
                            if isinstance(record_date, str):
                                record_date = datetime.fromisoformat(record_date)
                            if isinstance(record_date, datetime):
                                last_successful_date = record_date
                        except (ValueError, TypeError):
                            logger.debug(f"Could not parse updated date: {last_record.get('issue_data', {}).get('updated')}")
            
            logger.info(f"Successfully inserted {success_count} out of {len(history_records)} records")
            
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
                # Always use the last successful record date when available, since we don't know
                # if all records were fetched from JIRA (due to pagination, API limits, etc.)
                if last_successful_date:
                    self.update_sync_date(last_successful_date)
                    logger.info(f"Updated last sync date to last successful record date: {last_successful_date}")
                elif all_bulk_operations_succeeded and success_count == 0:
                    # Only use end_date if no records were processed but operations succeeded
                    # This handles the case where the date range had no data
                    self.update_sync_date(end_date)
                    logger.info(f"No records found in date range. Updated last sync date to {end_date}")
                else:
                    logger.warning("Could not determine last successful date. Not updating the sync date.")
            except Exception as e:
                logger.error(f"Error updating sync date: {e}")
        else:
            logger.warning("JIRA authorization failed. Not updating the sync date.")
        return success_count

    def document_exists_by_id_and_timestamp(self, doc_id, timestamp, index_name=INDEX_CHANGELOG):
        """
        Check if a document exists with the specified _id and @timestamp.
        
        Args:
            doc_id: The document ID to search for
            timestamp: The @timestamp datetime to match (can be string or datetime object)
            index_name: The index to search in (default: INDEX_CHANGELOG)
            
        Returns:
            bool: True if a document exists with the specified _id and @timestamp, False otherwise
        """
        try:
            if not self.connected:
                self.connect()
            
            # Convert timestamp to ISO format string if it's a datetime object
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)
            
            # Try to get the document by ID first
            response = requests.get(f"{self.base_url}/{index_name}/_doc/{doc_id}", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                # Document exists, now check if the @timestamp matches
                doc = response.json()
                source = doc.get('_source', {})
                doc_timestamp = source.get('@timestamp')
                
                if doc_timestamp:
                    # Normalize both timestamps for comparison
                    if isinstance(timestamp, datetime):
                        # If input is datetime, parse doc timestamp and compare as datetime objects
                        try:
                            doc_datetime = datetime.fromisoformat(doc_timestamp.replace('Z', '+00:00'))
                            # Convert to same timezone for comparison
                            if timestamp.tzinfo:
                                doc_datetime = doc_datetime.replace(tzinfo=timestamp.tzinfo)
                            return doc_datetime == timestamp
                        except (ValueError, TypeError):
                            # Fall back to string comparison
                            return doc_timestamp == timestamp_str
                    else:
                        # String comparison
                        return doc_timestamp == timestamp_str
                else:
                    logger.debug(f"Document {doc_id} exists but has no @timestamp field")
                    return False
                    
            elif response.status_code == 404:
                # Document doesn't exist
                logger.debug(f"Document {doc_id} not found in index {index_name}")
                return False
            else:
                logger.warning(f"Failed to check document existence: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False
      
    def get_database_summary(self, days=30):
        """
        Gets a summary of the data in Elasticsearch using HTTP requests.
        
        Args:
            days: Number of days to include in the summary (default: 30)
            
        Returns:
            dict: Summary statistics about the database
        """
        try:
            # Calculate the date range using the provided days parameter
            end_date = datetime.now(APP_TIMEZONE)
            start_date = end_date - timedelta(days=days)
            
            # Build the query
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": start_date.isoformat(),
                            "lte": end_date.isoformat()
                        }
                    }
                },
                "aggs": {
                    "total_records": {
                        "value_count": {
                            "field": "@timestamp"
                        }
                    },
                    "oldest_record": {
                        "min": {
                            "field": "@timestamp"
                        }
                    },
                    "newest_record": {
                        "max": {
                            "field": "@timestamp"
                        }
                    },
                    "unique_issues": {
                        "cardinality": {
                            "field": "issue.key.keyword"
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
            response = requests.post(f"{self.base_url}/{INDEX_CHANGELOG}/_search", 
                                   headers=self.headers, json=query, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to get database summary: {response.status_code}")
                return None
                
            result = response.json()
            
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
          
    def _extract_issue_identifier(self, record):
        """
        Extract issue identifier from comprehensive record for logging purposes.
        
        Args:
            record: Dictionary containing comprehensive record data
            
        Returns:
            str: Issue identifier for logging        """
        return record.get('issue_data', {}).get('key', 'unknown')

    def format_issue_record(self, issue_record):
        """
        Format an issue record for insertion into Elasticsearch.
        
        Args:
            issue_record: Dictionary containing the issue data
            
        Returns:
            Tuple: (formatted_document, document_id) for Elasticsearch
        """
        return ElasticsearchDocumentFormatter.format_issue_record(issue_record)

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
