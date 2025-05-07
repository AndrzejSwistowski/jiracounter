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
import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

# Get Elasticsearch settings from environment variables
# Format for ELASTIC_URL is expected to be: https://hostname:port
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
            # If full URL is provided, use it directly
            if self.url:
                logger.info(f"Connecting to Elasticsearch with URL: {self.url}")
                connect_args = {
                    'hosts': [self.url]
                }
            else:
                # Otherwise build connection from host/port
                logger.info(f"Connecting to Elasticsearch at {self.host}:{self.port}")
                connect_args = {
                    'hosts': [f'{"https" if self.use_ssl else "http"}://{self.host}:{self.port}']
                }
            
            # Add API key authentication if provided
            if self.api_key:
                connect_args['api_key'] = self.api_key
                logger.info("Using API key authentication")
                
            self.es = Elasticsearch(**connect_args)
            
            # Check connection
            if not self.es.ping():
                raise ConnectionError("Could not connect to Elasticsearch")
                
            logger.info("Successfully connected to Elasticsearch")
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
        """Creates the necessary indices in Elasticsearch if they don't exist."""
        try:
            # Check if the changelog index exists
            if not self.es.indices.exists(index=INDEX_CHANGELOG):
                # Define the mapping for changelog entries
                changelog_mapping = {
                    "mappings": {
                        "properties": {
                            "historyId": {"type": "keyword"},
                            "historyDate": {"type": "date"},
                            "factType": {"type": "integer"},
                            "issue": {
                                "properties": {
                                    "id": {"type": "keyword"},
                                    "key": {"type": "keyword"},
                                    "type": {
                                        "properties": {
                                            "name": {"type": "keyword"}
                                        }
                                    },
                                    "status": {
                                        "properties": {
                                            "name": {"type": "keyword"}
                                        }
                                    }
                                }
                            },
                            "assignee": {
                                "properties": {
                                    "username": {"type": "keyword"},
                                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                                }
                            },
                            "reporter": {
                                "properties": {
                                    "username": {"type": "keyword"},
                                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                                }
                            },
                            "allocation": {
                                "properties": {
                                    "code": {"type": "keyword"},
                                    "name": {"type": "keyword"}
                                }
                            },
                            "project": {
                                "properties": {
                                    "key": {"type": "keyword"},
                                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                                }
                            },
                            "parentKey": {"type": "keyword"},
                            "author": {
                                "properties": {
                                    "username": {"type": "keyword"},
                                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                                }
                            },
                            "changes": {
                                "type": "nested",
                                "properties": {
                                    "field": {"type": "keyword"},
                                    "from": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                                    "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                                }
                            }
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
                
                # Create the index
                self.es.indices.create(index=INDEX_CHANGELOG, body=changelog_mapping)
                logger.info(f"Created {INDEX_CHANGELOG} index")
            
            # Check if the settings index exists
            if not self.es.indices.exists(index=INDEX_SETTINGS):
                # Define the mapping for settings
                settings_mapping = {
                    "mappings": {
                        "properties": {
                            "agent_name": {"type": "keyword"},
                            "last_sync_date": {"type": "date"},
                            "last_updated": {"type": "date"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
                
                # Create the index
                self.es.indices.create(index=INDEX_SETTINGS, body=settings_mapping)
                logger.info(f"Created {INDEX_SETTINGS} index")
                
            return True
        except Exception as e:
            logger.error(f"Error creating indices: {e}")
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
                return datetime.fromisoformat(result["hits"]["hits"][0]["_source"]["last_sync_date"])
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
                    return datetime.fromisoformat(result["hits"]["hits"][0]["_source"]["historyDate"])
                
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
        Formats a history record for insertion into Elasticsearch.
        
        Args:
            history_record: Dictionary containing the issue history data
            
        Returns:
            Dictionary formatted for Elasticsearch insertion
        """
        # Create the basic document structure
        doc = {
            "historyId": history_record['historyId'],
            "historyDate": history_record['historyDate'].isoformat(),
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
                    logger.debug(f"Record with historyId {record['historyId']} already exists, skipping")
                    continue
                
                # Format the record for Elasticsearch
                doc = self.format_changelog_entry(record)
                
                # Add the action
                actions.append({
                    "_index": INDEX_CHANGELOG,
                    "_source": doc
                })
            
            # Execute the bulk operation
            if actions:
                success, failed = bulk(self.es, actions)
                logger.debug(f"Bulk insert: {success} succeeded, {failed} failed")
                return success
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
        
        # If no end_date provided, use current time
        if not end_date:
            end_date = datetime.now()
            
        logger.info(f"Populating Elasticsearch with JIRA data from {start_date} to {end_date}")
        
        # Get issue history records from JIRA
        history_records = self.jira_service.get_issue_history(start_date, end_date, max_issues)
        
        # Process records in bulk
        success_count = 0
        for i in range(0, len(history_records), bulk_size):
            batch = history_records[i:i+bulk_size]
            success_count += self.bulk_insert_issue_history(batch)
                
        # Update the last sync date
        self.update_sync_date(end_date)
        
        logger.info(f"Successfully inserted {success_count} out of {len(history_records)} records")
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
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
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