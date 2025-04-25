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
        days_since = (datetime.now().astimezone() - parsed_date).days
        return days_since
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing date {date_str}: {str(e)}")
        return 0