"""
Time utilities for the JiraCounter application.

This module provides standardized functions for handling dates and times,
ensuring consistent formatting throughout the application.
"""

import logging
from datetime import datetime, timezone, timedelta, time
import dateutil.parser
import pytz
import holidays

# Configure logging
logger = logging.getLogger(__name__)

# Default timezone to use for all operations
DEFAULT_TIMEZONE = timezone.utc

# Working hours configuration
WORK_START_HOUR = 9
WORK_END_HOUR = 17
MINUTES_PER_WORK_DAY = (WORK_END_HOUR - WORK_START_HOUR) * 60  # 480 minutes

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

def is_polish_holiday(date_obj):
    """
    Check if a given date is a Polish holiday.
    
    Args:
        date_obj: datetime object to check
        
    Returns:
        bool: True if the date is a Polish holiday, False otherwise
    """
    try:
        polish_holidays = holidays.Poland(years=date_obj.year)
        return date_obj.date() in polish_holidays
    except Exception as e:
        logger.error(f"Error checking Polish holiday for {date_obj}: {e}")
        return False

def is_working_day(date_obj):
    """
    Check if a given date is a working day (Monday-Friday, not a Polish holiday).
    
    Args:
        date_obj: datetime object to check
        
    Returns:
        bool: True if it's a working day, False otherwise
    """
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if date_obj.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if it's not a Polish holiday
    return not is_polish_holiday(date_obj)

def calculate_working_minutes_between(start_date, end_date):
    """
    Calculate the number of working minutes between two dates.
    Working week: Monday to Friday
    Working hours: 9:00 to 17:00 (480 minutes per day)
    Excludes Polish holidays.
    
    Args:
        start_date: Start datetime (datetime object or string)
        end_date: End datetime (datetime object or string)
        
    Returns:
        int: Number of working minutes between the dates, or None if input is invalid
    """
    if start_date is None or end_date is None:
        return None
        
    try:
        # Ensure we have datetime objects
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)
            
        if start_date is None or end_date is None:
            return None
            
        # Ensure start_date is before end_date
        if start_date > end_date:
            return 0
            
        total_minutes = 0
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date.date() <= end_date.date():
            if is_working_day(current_date):
                # Determine work start and end times for this day
                work_start = current_date.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
                work_end = current_date.replace(hour=WORK_END_HOUR, minute=0, second=0, microsecond=0)
                
                # Calculate actual work period for this day
                day_start = max(start_date, work_start)
                day_end = min(end_date, work_end)
                
                # Only count if there's overlap with working hours
                if day_start < day_end and day_start.time() < time(WORK_END_HOUR) and day_end.time() > time(WORK_START_HOUR):
                    # Ensure times are within working hours
                    if day_start.time() < time(WORK_START_HOUR):
                        day_start = day_start.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
                    if day_end.time() > time(WORK_END_HOUR):
                        day_end = day_end.replace(hour=WORK_END_HOUR, minute=0, second=0, microsecond=0)
                    
                    # Calculate minutes for this day
                    if day_start < day_end:
                        day_minutes = int((day_end - day_start).total_seconds() / 60)
                        total_minutes += day_minutes
            
            current_date += timedelta(days=1)
            
        return total_minutes
        
    except Exception as e:
        logger.error(f"Error calculating working minutes: {e}")
        return None

def calculate_working_minutes_since_date(date_string):
    """
    Calculate the number of working minutes between a given date and now.
    
    Args:
        date_string: Date string in any reasonable format
        
    Returns:
        int: Number of working minutes since the given date, or None if date_string is None
    """
    if not date_string:
        return None
        
    try:
        start_date = parse_date(date_string)
        if start_date is None:
            return None
        return calculate_working_minutes_between(start_date, now())
    except Exception as e:
        logger.error(f"Error calculating working minutes since date: {e}")
        return None
