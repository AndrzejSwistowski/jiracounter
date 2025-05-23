"""
Configuration settings for the Jira counter application.

This module provides configuration variables used throughout the application.
Environment variables can be used to override default settings.
"""
import os
from typing import Optional

# Jira connection settings
JIRA_BASE_URL = os.environ.get('JIRA_BASE_URL', 'https://voyager-team.atlassian.net')
JIRA_USERNAME = os.environ.get('JIRA_USERNAME', 'andrzej.swistowski@voyager.pl')
JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN', '')  # Use API token instead of password for security

# Jira custom field mappings
JIRA_CUSTOM_FIELDS = {
    'RODZAJ_PRACY': 'customfield_10138',
    'DATA_ZMIANY_STATUSU': 'customfield_10070'  # Correct field ID found in Jira instance
}

# Application behavior
CACHE_DURATION = int(os.environ.get('JIRA_CACHE_DURATION', '3600'))  # Cache duration in seconds
LOG_LEVEL = os.environ.get('JIRA_LOG_LEVEL', 'INFO')

# Paths
DATA_DIR = os.environ.get('JIRA_DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Elasticsearch connection settings
ELASTIC_URL = os.environ.get('ELASTIC_URL')
ELASTIC_APIKEY = os.environ.get('ELASTIC_APIKEY')

# Default Elasticsearch connection settings if environment variables not set
ES_HOST = "localhost"
ES_PORT = 9200
ES_USE_SSL = False

# Parse ELASTIC_URL if provided to extract host, port, and protocol
if ELASTIC_URL:
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(ELASTIC_URL)
        ES_HOST = parsed_url.hostname or ES_HOST
        ES_PORT = parsed_url.port or ES_PORT
        ES_USE_SSL = parsed_url.scheme == 'https'
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error parsing ELASTIC_URL: {e}. Using defaults.")

# Elasticsearch index names
INDEX_CHANGELOG = "jira-changelog"
INDEX_SETTINGS = "jira-settings"

def get_credentials() -> tuple[str, Optional[str]]:
    """Return the username and API token as a tuple.
    
    Returns:
        tuple: (username, api_token)
    """
    return JIRA_USERNAME, JIRA_API_TOKEN

def get_elasticsearch_config() -> dict:
    """Return Elasticsearch connection configuration as a dictionary.
    
    Returns:
        dict: Configuration containing url, host, port, use_ssl, api_key
    """
    return {
        'url': ELASTIC_URL,
        'host': ES_HOST,
        'port': ES_PORT,
        'use_ssl': ES_USE_SSL,
        'api_key': ELASTIC_APIKEY
    }

# If this module is run directly, print the current configuration
if __name__ == "__main__":
    print("Current Jira configuration:")
    print(f"  JIRA_BASE_URL: {JIRA_BASE_URL}")
    print(f"  JIRA_USERNAME: {JIRA_USERNAME}")
    print(f"  LOG_LEVEL: {LOG_LEVEL}")
    print(f"  DATA_DIR: {DATA_DIR}")
    print("\nElasticsearch configuration:")
    print(f"  ELASTIC_URL: {ELASTIC_URL}")
    print(f"  ES_HOST: {ES_HOST}")
    print(f"  ES_PORT: {ES_PORT}")
    print(f"  ES_USE_SSL: {ES_USE_SSL}")
    print(f"  INDEX_CHANGELOG: {INDEX_CHANGELOG}")
    print(f"  INDEX_SETTINGS: {INDEX_SETTINGS}")
