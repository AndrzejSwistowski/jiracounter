"""Utility functions for the Jira Licznik application."""

import logging
from datetime import datetime
import dateutil.parser
from typing import Optional

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