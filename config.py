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


# Application behavior
CACHE_DURATION = int(os.environ.get('JIRA_CACHE_DURATION', '3600'))  # Cache duration in seconds
LOG_LEVEL = os.environ.get('JIRA_LOG_LEVEL', 'INFO')

# Paths
DATA_DIR = os.environ.get('JIRA_DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def get_credentials() -> tuple[str, Optional[str]]:
    """Return the username and API token as a tuple.
    
    Returns:
        tuple: (username, api_token)
    """
    return JIRA_USERNAME, JIRA_API_TOKEN

# If this module is run directly, print the current configuration
if __name__ == "__main__":
    print("Current Jira configuration:")
    print(f"  JIRA_BASE_URL: {JIRA_BASE_URL}")
    print(f"  JIRA_USERNAME: {JIRA_USERNAME}")
    print(f"  LOG_LEVEL: {LOG_LEVEL}")
    print(f"  DATA_DIR: {DATA_DIR}")
