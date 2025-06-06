"""
Reset the last sync date in the Elasticsearch jira-settings index.

This script will:
1. Connect to Elasticsearch
2. Find the current sync date in the jira-settings index
3. Reset the sync date to a specific date or delete the entry entirely
4. Allow for full repopulation of the jira-changelog index

Run this script before repopulating the Elasticsearch index after structural changes.
"""

import logging
import sys
import json
import requests
from datetime import datetime, timedelta
import config
from es_utils import _setup_es_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("es_reset_sync_date.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

AGENT_NAME = "JiraETLAgent"  # Default agent name used in the settings index

def connect_elasticsearch():
    """Establishes a connection to Elasticsearch."""
    try:
        es_config = config.get_elasticsearch_config()
        
        # Setup connection using centralized helper
        url, headers = _setup_es_connection(
            host=es_config['host'],
            port=es_config['port'],
            api_key=es_config['api_key'],
            use_ssl=es_config.get('use_ssl', False),
            url=es_config['url']
        )
        
        if es_config['api_key']:
            logger.info("Using API key authentication")
        
        # Test the connection by requesting cluster health
        response = requests.get(f"{url}/_cluster/health", headers=headers)
        
        if response.status_code != 200:
            raise ConnectionError(f"Could not connect to Elasticsearch: {response.status_code} - {response.text}")
            
        health_data = response.json()
        logger.info(f"Successfully connected to Elasticsearch cluster: {health_data['cluster_name']} / Status: {health_data['status']}")
        
        return url, headers
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        raise

def get_current_sync_date(url, headers, agent_name=AGENT_NAME):
    """Get the current last_sync_date from the settings index."""
    try:
        # Check if the settings index exists
        index_response = requests.head(f"{url}/{config.INDEX_SETTINGS}", headers=headers)
        if index_response.status_code != 200:
            logger.warning(f"Settings index {config.INDEX_SETTINGS} does not exist")
            return None, None
        
        # Query to find the settings document for the specified agent
        query = {
            "query": {
                "term": {
                    "agent_name": agent_name
                }
            }
        }
        
        search_response = requests.post(f"{url}/{config.INDEX_SETTINGS}/_search", headers=headers, json=query)
        
        if search_response.status_code != 200:
            logger.error(f"Failed to search settings index: {search_response.status_code}")
            return None, None
            
        result = search_response.json()
        
        if result["hits"]["total"]["value"] > 0:
            hit = result["hits"]["hits"][0]
            doc_id = hit["_id"]
            last_sync_date = hit["_source"].get("last_sync_date")
            
            if last_sync_date:
                logger.info(f"Found last_sync_date: {last_sync_date}")
                return doc_id, last_sync_date
            else:
                logger.warning("Document found but last_sync_date is not set")
                return doc_id, None
        else:
            logger.warning(f"No settings document found for agent: {agent_name}")
            return None, None
    except Exception as e:
        logger.error(f"Error retrieving current sync date: {e}")
        return None, None

def reset_sync_date(url, headers, doc_id=None, new_date=None, delete_doc=False, agent_name=AGENT_NAME):
    """Reset the last_sync_date in the settings index."""
    try:
        if delete_doc and doc_id:
            # Delete the document
            delete_response = requests.delete(f"{url}/{config.INDEX_SETTINGS}/_doc/{doc_id}", headers=headers)
            if delete_response.status_code in [200, 404]:
                logger.info(f"Deleted settings document with ID {doc_id}")
                return True
            else:
                logger.error(f"Failed to delete document: {delete_response.status_code}")
                return False
            
        elif doc_id:
            # Update the existing document with a new date
            if not new_date:
                # Default to 30 days ago if no date provided
                new_date = (datetime.now() - timedelta(days=30)).isoformat()
                
            # Prepare the update document
            update_doc = {
                "doc": {
                    "last_sync_date": new_date,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            update_response = requests.post(f"{url}/{config.INDEX_SETTINGS}/_update/{doc_id}", headers=headers, json=update_doc)
            if update_response.status_code == 200:
                logger.info(f"Updated last_sync_date to {new_date}")
                return True
            else:
                logger.error(f"Failed to update document: {update_response.status_code}")
                return False
            
        elif not delete_doc:
            # Create a new document if one doesn't exist
            doc = {
                "agent_name": agent_name,
                "last_sync_date": new_date or (datetime.now() - timedelta(days=30)).isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            create_response = requests.post(f"{url}/{config.INDEX_SETTINGS}/_doc", headers=headers, json=doc)
            if create_response.status_code in [200, 201]:
                logger.info(f"Created new settings document with last_sync_date: {doc['last_sync_date']}")
                return True
            else:
                logger.error(f"Failed to create document: {create_response.status_code}")
                return False
            
        return False
    except Exception as e:
        logger.error(f"Error resetting sync date: {e}")
        return False

def main():
    """Main function to reset the sync date."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset the Elasticsearch jira-settings index sync date")
    parser.add_argument("--days", type=int, default=30, help="Number of days to set the sync date back (default: 30)")
    parser.add_argument("--delete", action="store_true", help="Delete the settings document instead of updating it")
    parser.add_argument("--agent", type=str, default=AGENT_NAME, help=f"Agent name in settings index (default: {AGENT_NAME})")
    parser.add_argument("--date", type=str, help="Specific date to set (format: YYYY-MM-DDTHH:MM:SS, overrides --days)")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    try:
        # Connect to Elasticsearch
        url, headers = connect_elasticsearch()
        
        # Get the current sync date
        doc_id, current_date = get_current_sync_date(url, headers, args.agent)
        
        if current_date:
            logger.info(f"Current sync date for agent '{args.agent}' is {current_date}")
        else:
            logger.info(f"No sync date found for agent '{args.agent}'")
        
        # Calculate the new sync date if not using delete option
        new_date = None
        if not args.delete and not args.date:
            new_date = (datetime.now() - timedelta(days=args.days)).isoformat()
            logger.info(f"Will reset sync date to {new_date} ({args.days} days ago)")
        elif args.date:
            new_date = args.date
            logger.info(f"Will reset sync date to specified date: {new_date}")
        
        # Confirm action with the user
        if not args.yes:
            if args.delete:
                action = "delete the settings document"
            else:
                action = f"reset the sync date to {new_date}"
                
            confirm = input(f"Are you sure you want to {action}? (y/n): ")
            
            if confirm.lower() != 'y':
                logger.info("Operation cancelled by user")
                return False
        
        # Reset the sync date
        success = reset_sync_date(url, headers, doc_id, new_date, args.delete, args.agent)
        
        if success:
            logger.info("Successfully reset sync date")
            logger.info("You can now run repopulate_es.py to repopulate the index")
            return True
        else:
            logger.error("Failed to reset sync date")
            return False
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
