# Logger Utils Documentation

## Overview
The `logger_utils.py` module provides centralized logging functionality for the JIRA counter application. 
This helps maintain consistent logging across all scripts and avoids code duplication.

## Usage

### Basic Usage
```python
from logger_utils import setup_logging

# Get a logger with default settings
logger = setup_logging()
logger.info("This is an info message")
logger.debug("This is a debug message - only shown in verbose mode")
logger.error("This is an error message")
```

### Customized Usage
```python
from logger_utils import setup_logging

# Customize the logger
logger = setup_logging(
    verbose=True,                # Enable debug logging  
    log_prefix="my_script",      # Custom log file prefix
    log_dir="custom_logs",       # Custom log directory
    use_timestamp=True,          # Add timestamp to log filename
    log_to_file=True,            # Log to file
    log_to_console=True,         # Log to console
    quiet_libraries=True         # Reduce log noise from common libraries
)
```

### Parameters

- `logger_name`: The name for the logger (defaults to calling module name)
- `verbose`: Whether to use DEBUG level (defaults to INFO level)
- `log_prefix`: Prefix for the log filename
- `log_dir`: Directory for log files
- `use_timestamp`: Whether to add timestamp to log filename
- `log_to_file`: Whether to log to file
- `log_to_console`: Whether to log to console
- `quiet_libraries`: Whether to reduce log noise from common libraries

## Example Implementation
Here's how it's used in the `populate_es.py` script:

```python
from logger_utils import setup_logging

# In the main function
logger = setup_logging(
    verbose=args.verbose,
    log_prefix="jira_etl_es"
)
logger.info("Starting JIRA to Elasticsearch ETL process")
```
