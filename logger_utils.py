#!/usr/bin/env python3
"""
Centralized logging utilities for the JIRA counter application.
This module provides common logging functionality to be used across all scripts.
"""

import logging
import os
from datetime import datetime

def setup_logging(
    logger_name=None,
    verbose=False, 
    log_prefix="app",
    log_dir="logs",
    use_timestamp=True,
    log_to_file=True,
    log_to_console=True,
    quiet_libraries=True
):
    """
    Configure logging for application components.
    
    Args:
        logger_name (str, optional): The name for the logger. If None, uses __name__ from caller.
        verbose (bool, optional): Whether to use DEBUG level. Defaults to False (INFO level).
        log_prefix (str, optional): Prefix for the log filename. Defaults to "app".
        log_dir (str, optional): Directory for log files. Defaults to "logs".
        use_timestamp (bool, optional): Whether to add timestamp to log filename. Defaults to True.
        log_to_file (bool, optional): Whether to log to file. Defaults to True.
        log_to_console (bool, optional): Whether to log to console. Defaults to True.
        quiet_libraries (bool, optional): Whether to reduce log noise from common libraries. Defaults to True.
    
    Returns:
        Logger: Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if it doesn't exist and log_to_file is True
    if log_to_file and log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Build handlers list
    handlers = []
    
    # Add file handler if requested
    if log_to_file:
        # Generate log filename
        if use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{log_dir}/{log_prefix}_{timestamp}.log"
        else:
            log_filename = f"{log_dir}/{log_prefix}.log"
        
        handlers.append(logging.FileHandler(log_filename))
    
    # Add console handler if requested
    if log_to_console:
        handlers.append(logging.StreamHandler())
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Get the logger
    if logger_name is None:
        # This gets the name of the module that called this function
        import inspect
        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0])
        logger_name = caller_module.__name__ if caller_module else '__main__'
    
    logger = logging.getLogger(logger_name)
    
    # Reduce noise from other libraries if requested
    if quiet_libraries:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    
    # Log the file location if we're logging to a file
    if log_to_file:
        logger.info(f"Log file: {log_filename}")
    
    return logger
