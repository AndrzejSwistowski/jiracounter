"""
Time utilities for the JiraCounter application.

This module provides standardized functions for handling dates and times,
ensuring consistent formatting throughout the application.
"""

import logging
from datetime import datetime, timezone, timedelta
import dateutil.parser
import pytz

# Configure logging
logger = logging.getLogger(__name__)

# Default timezone to use for all operations
DEFAULT_TIMEZONE = timezone.utc

def to_iso8601(date_value):
    """
    Convert any date/time value to ISO8601 format with timezone information.
    
    Args:
        date_value: A datetime object, ISO8601 string, or other date representation
        
    Returns:
        str: Date in ISO8601 format with timezone information
    """
    if date_value is None:
        return None
        
    try:
        # If it's already a string, try to parse it
        if isinstance(date_value, str):
            dt = dateutil.parser.parse(date_value)
        else:
            dt = date_value
            
        # Ensure timezone information is present
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEFAULT_TIMEZONE)
            
        # Return in ISO8601 format
        return dt.isoformat()
    except Exception as e:
        logger.error(f"Error converting to ISO8601: {e}")
        return None

def parse_date(date_string):
    """
    Parse a date string into a datetime object with timezone.
    
    Args:
        date_string: Date string in any reasonable format
        
    Returns:
        datetime: Datetime object with timezone information
    """
    if not date_string:
        return None
        
    try:
        dt = dateutil.parser.parse(date_string)
        # Ensure timezone information is present
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEFAULT_TIMEZONE)
        return dt
    except Exception as e:
        logger.error(f"Error parsing date '{date_string}': {e}")
        return None

def calculate_working_days_between(start_date, end_date):
    """
    Calculate the number of working days between two dates.
    
    Args:
        start_date: Start date (datetime or string)
        end_date: End date (datetime or string)
        
    Returns:
        float: Number of working days between the dates
    """
    if start_date is None or end_date is None:
        return None
        
    try:
        # Ensure we have datetime objects
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)
            
        # Count business days
        days = 0
        current_date = start_date
        while current_date <= end_date:
            # Check if it's a weekday (Monday = 0, Sunday = 6)
            if current_date.weekday() < 5:  # Monday-Friday
                days += 1
            current_date += timedelta(days=1)
            
        return days
    except Exception as e:
        logger.error(f"Error calculating working days: {e}")
        return None

def now():
    """
    Get current datetime with timezone information.
    
    Returns:
        datetime: Current datetime with timezone information
    """
    return datetime.now(DEFAULT_TIMEZONE)

def format_for_jql(date_value):
    """
    Format a date for use in JQL queries.
    
    Args:
        date_value: Datetime object or string
        
    Returns:
        str: Date formatted for JQL (yyyy-MM-dd HH:mm)
    """
    if date_value is None:
        return None
        
    try:
        # Ensure we have a datetime object
        if isinstance(date_value, str):
            dt = parse_date(date_value)
        else:
            dt = date_value
            
        # Return in JQL format
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        logger.error(f"Error formatting date for JQL: {e}")
        return None

def find_status_change_date(change_history, status_name, default=None):
    """
    Find the date when an issue transitioned to a specific status.
    
    Args:
        change_history: List of changelog entries
        status_name: Status name to find
        default: Default value if not found
        
    Returns:
        datetime: Date when the issue changed to the specified status, or default if not found
    """
    if not change_history or not status_name:
        return default
        
    for history in change_history:
        for change in history['changes']:
            if change['field'] == 'status' and change['to'] == status_name:
                return history['historyDate']
    
    return default

def find_first_status_change_date(change_history, default=None):
    """
    Find the date of the first status change in an issue's history.
    
    Args:
        change_history: List of changelog entries
        default: Default value if not found
        
    Returns:
        datetime: Date of the first status change, or default if not found
    """
    if not change_history:
        return default
        
    for history in change_history:
        for change in history['changes']:
            if change['field'] == 'status':
                return history['historyDate']
    
    return default

def calculate_days_since_date(date_string):
    """
    Calculate the number of days between a given date and now.
    
    Args:
        date_string: Date string in ISO8601 format
        
    Returns:
        float: Number of days since the given date, or None if date_string is None
    """
    if not date_string:
        return None
        
    try:
        date = parse_date(date_string)
        return calculate_working_days_between(date, now())
    except Exception as e:
        logger.error(f"Error calculating days since date: {e}")
        return None
