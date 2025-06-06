"""Utility functions for various operations in the JiraCounter application.

Contains helper functions for date calculations, string manipulations, and other common tasks.
"""

import logging
from datetime import datetime, timedelta, timezone
import dateutil.parser
import pytz
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a single, application-wide timezone (using UTC as the standard)
# All internal processing will use UTC, only converting for display/user-facing output
APP_TIMEZONE = pytz.timezone('Europe/Warsaw')  # Change to your preferred timezone, e.g., pytz.timezone('Europe/Warsaw')

def parse_date_with_timezone(date_str: str) -> datetime:
    """
    Parse a date string and ensure it has timezone information.
    
    Args:
        date_str: The date string to parse
        
    Returns:
        datetime: A timezone-aware datetime object in UTC
    """
    try:
        parsed_date = dateutil.parser.parse(date_str)
        # If the parsed date doesn't have timezone info, add UTC
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=APP_TIMEZONE)
        else:
            # Ensure all dates are in UTC for internal consistency
            parsed_date = parsed_date.astimezone(APP_TIMEZONE)
        return parsed_date
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        # Return current time with timezone if parsing fails
        return datetime.now(APP_TIMEZONE)

def calculate_days_since_date(date_str: str) -> int:
    """Calculate the number of days between a given date and the current date.
    
    Args:
        date_str: The date string to parse
        
    Returns:
        Integer representing the number of days since the given date
    """
    if not date_str:
        return None
        
    try:
        # Parse date and ensure it's in UTC
        parsed_date = parse_date_with_timezone(date_str)
        # Get current time in APP_TIMEZONE
        now = datetime.now(APP_TIMEZONE)
        # Calculate days
        days_since = (now - parsed_date).days
        return days_since
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing date {date_str}: {str(e)}")
        return 0

def calculate_working_days_between(start_date, end_date=None):
    """Calculate the number of working days (Monday to Friday) between two dates.
    
    Args:
        start_date: Start date (string or datetime)
        end_date: End date (string or datetime), defaults to now if None
        
    Returns:
        float: Number of working days between the dates
    """
    if not start_date:
        return None
        
    try:
        # Parse the start date if it's a string
        if isinstance(start_date, str):
            from dateutil import parser
            start_obj = parser.parse(start_date)
        else:
            start_obj = start_date
            
        # Parse or set the end date
        if end_date:
            if isinstance(end_date, str):
                from dateutil import parser
                end_obj = parser.parse(end_date)
            else:
                end_obj = end_date
        else:
            end_obj = datetime.now(pytz.UTC)
            
        # Make sure both dates have timezone information
        if start_obj.tzinfo is None:
            start_obj = start_obj.replace(tzinfo=pytz.UTC)
            
        if end_obj.tzinfo is None:
            end_obj = end_obj.replace(tzinfo=pytz.UTC)
            
        # Ensure start_date is before end_date
        if start_obj > end_obj:
            return 0
            
        # Calculate working days
        working_days = 0
        current_date = start_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Count full working days
        while current_date < end_date:
            # Weekday returns 0 (Monday) through 6 (Sunday)
            if current_date.weekday() < 5:  # Monday to Friday
                working_days += 1
            current_date += timedelta(days=1)
            
        # For partial days (if start and end are on the same day)
        if start_obj.date() == end_obj.date() and start_obj.weekday() < 5:
            # Calculate fraction of the working day
            work_hours = 8  # Assuming 8-hour workday from 9am to 5pm
            start_hour = max(9, min(17, start_obj.hour + start_obj.minute/60))
            end_hour = max(9, min(17, end_obj.hour + end_obj.minute/60))
            
            if start_hour < 17 and end_hour > 9:
                fraction = (min(17, end_hour) - max(9, start_hour)) / work_hours
                working_days = max(0, fraction)  # Use the fraction instead of adding a full day
                
        # For partial start day
        elif start_obj.weekday() < 5:
            # Calculate fraction of remaining work day
            work_hours = 8  # Assuming 8-hour workday
            start_hour = start_obj.hour + start_obj.minute/60
            
            if start_hour < 17:  # Only count if start is before end of workday
                fraction = (17 - max(9, start_hour)) / work_hours
                working_days -= (1 - fraction)  # Subtract unused portion of the day
                
        # For partial end day
        if start_obj.date() != end_obj.date() and end_obj.weekday() < 5:
            # Calculate fraction of end work day
            work_hours = 8  # Assuming 8-hour workday
            end_hour = end_obj.hour + end_obj.minute/60
            
            if end_hour > 9:  # Only count if end is after start of workday
                fraction = (min(17, end_hour) - 9) / work_hours
                working_days -= (1 - fraction)  # Subtract unused portion of the day
                
        return round(working_days, 1)  # Round to 1 decimal place for readability
    except Exception as e:
        logger.error(f"Error calculating working days between dates: {e}")
        return None



def find_first_status_change_date(issue_history):
    """Find the date when an issue had its first status change.
    
    Args:
        issue_history: List of changelog entries for the issue
        
    Returns:
        datetime: The date of the first status change, or None if no status changes found
    """
    if not issue_history:
        return None
        
    # Sort history by date, oldest first (to find first move)
    sorted_history = sorted(issue_history, key=lambda x: x.get('historyDate', ''))
    
    # Find the first status change of any kind
    for entry in sorted_history:
        for change in entry.get('changes', []):
            if change.get('field') == 'status':
                logger.debug(f"Found first status change: {change.get('from')} -> {change.get('to')}")
                return entry.get('historyDate')
                
    return None

def validate_and_format_dates(start_date: str, end_date: str) -> Tuple[str, str]:
    """Validate and format date strings for use in JQL queries.
    
    Args:
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD
        
    Returns:
        Tuple of formatted start and end dates
        
    Raises:
        ValueError: If the date format is invalid
    """
    try:
        # Parse dates and ensure they're in the correct format
        start_date_obj = dateutil.parser.parse(start_date)
        end_date_obj = dateutil.parser.parse(end_date)
        
        # Format for JQL (inclusive of the start date, exclusive of the end date)
        formatted_start = start_date_obj.strftime("%Y-%m-%d")
        
        # Add one day to end_date to make the query inclusive of the end date
        end_date_obj = end_date_obj + timedelta(days=1)
        formatted_end = end_date_obj.strftime("%Y-%m-%d")
        
        return formatted_start, formatted_end
        
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD format: {str(e)}")

def format_date_for_jql(date_obj: datetime) -> str:
    """Format a datetime object for use in JQL queries.
    
    Args:
        date_obj: A datetime object
        
    Returns:
        String formatted for JQL (YYYY-MM-DD HH:MM:SS)
    """
    if not date_obj:
        return None
        
    try:
        if isinstance(date_obj, str):
            date_obj = parse_date_with_timezone(date_obj)
            
        # Ensure the date is timezone-aware
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(tzinfo=APP_TIMEZONE)
            
        # Format for JQL
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error formatting date for JQL: {e}")
        return None

def format_date_polish(date_str: str) -> str:
    """Format a date string into Polish format (e.g., '24 kwietnia 2025').
    
    Args:
        date_str: The date string to parse and format
        
    Returns:
        String formatted in Polish (day month_name year)
    """
    if not date_str:
        return ""
        
    try:
        # Parse the date
        parsed_date = parse_date_with_timezone(date_str)
        
        # Dictionary of Polish month names
        polish_months = {
            1: "stycznia",
            2: "lutego",
            3: "marca",
            4: "kwietnia",
            5: "maja",
            6: "czerwca",
            7: "lipca",
            8: "sierpnia",
            9: "września",
            10: "października",
            11: "listopada",
            12: "grudnia"
        }
        
        # Format the date in Polish
        day = parsed_date.day
        month = polish_months[parsed_date.month]
        year = parsed_date.year
        
        return f"{day} {month} {year}"
    except Exception as e:
        logger.error(f"Error formatting date in Polish: {e}")
        return date_str

def normalize_status_name(status_name: str) -> str:
    """
    Normalize legacy status names to standardized status names.
    
    This function maps various legacy status names (including typos, different languages,
    and old naming conventions) to their current standardized equivalents.
    
    Args:
        status_name: The original status name from JIRA
        
    Returns:
        Normalized status name
    """
    if not status_name:
        return status_name
        
    # Convert to lowercase for case-insensitive matching
    status_lower = status_name.lower().strip()
    
    # Define legacy to new status name mappings
    status_mapping = {
        # Polish to English mappings            
        'do poprawy': 'In Review',
        'testy wewnętrzne': 'Testing',
        'powiadomienie klienta': 'Customer Notification',
        'anulowane': 'Canceled',
        'ukończone': 'Completed',
        'zamknięte': 'Closed',
        'otwarte': 'Open',
        'w trakcie': 'In Progress',
        'in progress2': 'In Progress',  # Legacy name variation
        'oczekuje': 'Waiting',
        'planowane': 'Planned',
        'wybrane do realizacji': 'Selected for Development',
        'do zrobienia': 'Selected for Development',  # Polish legacy name
        'gotowe do przeglądu': 'Ready for Review',
        'gotowe do testów': 'Ready for Testing',
        'oczekuje na wydanie produkcyjne': 'Awaiting Production Release',
        
        # Legacy English variations
        'todo': 'Selected for Development',
        'to do': 'Selected for Development',
        'new': 'Open',
        'reopened': 'Open',            
        'resolved': 'Completed',
        
        # Common typos and variations
        'in progres': 'In Progress',
        'inprogress': 'In Progress',
        'in-progress': 'In Progress',
        'in_progress': 'In Progress',
        'in review': 'In Review',
        'inreview': 'In Review',
        'in-review': 'In Review',
        'in_review': 'In Review',
        'ready for review': 'Ready for Review',
        'ready_for_review': 'Ready for Review',
        'ready-for-review': 'Ready for Review',
        'ready for testing': 'Ready for Testing',
        'ready_for_testing': 'Ready for Testing',
        'ready-for-testing': 'Ready for Testing',
        'selected for development': 'Selected for Development',
        'selected_for_development': 'Selected for Development',
        'selected-for-development': 'Selected for Development',
        'awaiting production release': 'Awaiting Production Release',
        'awaiting_production_release': 'Awaiting Production Release',
        'awaiting-production-release': 'Awaiting Production Release',
        'customer notification': 'Customer Notification',
        'customer_notification': 'Customer Notification',
        'customer-notification': 'Customer Notification',
        
        # Status variations
        'hold': 'Hold',
        'on hold': 'Hold',
        'on-hold': 'Hold',
        'on_hold': 'Hold',
        'blocked': 'Blocked',
        'waiting': 'Waiting',
        'pending': 'Waiting',
        'draft': 'Draft',
        'backlog': 'Backlog',
        'open': 'Open',
        'planned': 'Planned',
        'testing': 'Testing',
        'completed': 'Completed',
        'canceled': 'Canceled'
    }
    
    # Return mapped status or original if no mapping found
    normalized = status_mapping.get(status_lower, status_name)
    
    # Log when we're using a mapping for debugging purposes
    if normalized != status_name:
        logger.debug(f"Normalized status '{status_name}' to '{normalized}'")
        
    return normalized