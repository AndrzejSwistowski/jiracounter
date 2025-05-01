"""Utility functions for the Jira Licznik application."""

import logging
from datetime import datetime, timedelta
import dateutil.parser
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_days_since_date(date_str: str) -> int:
    """Calculate the number of days between a given date and the current date.
    
    Args:
        date_str: The date string to parse
        
    Returns:
        Integer representing the number of days since the given date
    """
    try:
        parsed_date = dateutil.parser.parse(date_str)
        # Make sure both datetimes are either offset-aware or offset-naive
        now = datetime.now()
        if parsed_date.tzinfo is not None:
            # If parsed_date has timezone info, make sure now has it too
            now = now.astimezone()
        else:
            # If parsed_date has no timezone, remove it from now if present
            parsed_date = parsed_date.replace(tzinfo=None)
            now = now.replace(tzinfo=None)
            
        days_since = (now - parsed_date).days
        return days_since
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing date {date_str}: {str(e)}")
        return 0

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