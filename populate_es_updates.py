"""
This is a documentation file that demonstrates how to refactor the code to align with SOLID principles.
It shows the changes needed to address the issue with the log_progress function.
"""

"""
REFACTORING APPROACH:

1. Create a ProgressTracker class in progress_tracker.py (already done)
2. Modify JiraElasticsearchPopulator in es_populate.py to use ProgressTracker
3. Keep backward compatibility with the log_progress function

Here are example code snippets showing how to use ProgressTracker in populate_from_jira:
"""

# Example code for populate_from_jira method:
def populate_from_jira(self, start_date=None, end_date=None, max_issues=None, bulk_size=100):
    """
    Fetches data from JIRA and populates Elasticsearch.
    
    Args:
        start_date: The date to start fetching from (default: last sync date)
        end_date: The date to fetch up to (default: now)
        max_issues: Maximum number of issues to process (default: no limit)
        bulk_size: Number of records to insert in each bulk operation
        
    Returns:
        int: Number of records successfully inserted
    """
    # Connect if needed
    if not self.es:
        self.connect()
    
    # If no start_date provided, get the last sync date
    if not start_date:
        start_date = self.get_last_sync_date()
    
    # If no end_date provided, use current time in UTC
    if not end_date:
        end_date = datetime.now(APP_TIMEZONE)
        
    logger.info(f"Populating Elasticsearch with JIRA data from {start_date} to {end_date}")
    
    # Flag to track if we successfully connected to JIRA
    jira_connected = False
    # Flag to track if all bulk operations succeeded
    all_bulk_operations_succeeded = True
    success_count = 0
    
    try:
        # Reset the progress tracker at the start of a new populate operation
        self.progress_tracker.reset()
        
        # Get issue history records from JIRA
        result = self.jira_service.get_issue_history(
            start_date=start_date, 
            end_date=end_date, 
            max_issues=max_issues
        )
        
        if result is None:
            history_records = []
        else:
            history_records = result
            
        # If we get here, JIRA authentication was successful
        jira_connected = True
        
        # Process records in bulk
        bulk_data = []
        current_bulk_idx = 0
        total_inserted = 0
        
        # Track the last successfully processed history date
        last_successful_date = None
        
        # Log the total number of records to process
        logger.info(f"Found {len(history_records)} history records to process")
        total_records = len(history_records)
        
        # Process records in batches
        for i in range(0, len(history_records), bulk_size):
            batch = history_records[i:i+bulk_size]
            inserted_count = self.bulk_insert_issue_history(batch)
            total_inserted += inserted_count
            
            # Update progress after each batch
            self.progress_tracker.update(
                increment=len(batch), 
                total=total_records,
                interval=30
            )
            
            # If nothing was inserted in this batch, there might be an issue
            if inserted_count == 0 and len(batch) > 0:
                all_bulk_operations_succeeded = False
                logger.warning(f"Batch insert failed - 0 records inserted out of {len(batch)}")
                break
            
            # Update the last successful date if records were inserted
            if inserted_count > 0 and batch:
                last_record = batch[-1]
                if last_record.get('historyDate'):
                    try:
                        record_date = (
                            datetime.fromisoformat(last_record['historyDate']) 
                            if isinstance(last_record['historyDate'], str) 
                            else last_record['historyDate']
                        )
                        if isinstance(record_date, datetime):
                            last_successful_date = record_date
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse historyDate: {last_record.get('historyDate')}")
        
        # Log final progress with force_log=True to ensure it's displayed
        self.progress_tracker.update(increment=0, total=len(history_records), force_log=True)
        
        # Log summary of operation
        logger.info(f"Successfully inserted {total_inserted} out of {len(history_records)} records")
        logger.info(f"Average processing rate: {self.progress_tracker.items_per_second:.2f} items/sec")
        
        success_count = total_inserted
        
    except Exception as e:
        logger.error(f"Error fetching data from JIRA: {e}")
        all_bulk_operations_succeeded = False
    
    # Early exit if nothing was processed successfully
    if success_count == 0:
        logger.warning("No records were processed successfully. Exiting without updating sync date.")
        return 0
        
    # Determine what date to use for the sync
    if jira_connected:
        try:
            if all_bulk_operations_succeeded:
                # Use the end_date if all operations succeeded
                self.update_sync_date(end_date)
                logger.info(f"Updated last sync date to {end_date}")
            else:
                # Use the last successful history date if any operation failed
                if last_successful_date:
                    self.update_sync_date(last_successful_date)
                    logger.info(f"Bulk operations had failures. Updated last sync date to last successful record date: {last_successful_date}")
                else:
                    logger.warning("Could not determine last successful date. Not updating the sync date.")
        except Exception as e:
            logger.error(f"Error updating sync date: {e}")
    else:
        logger.warning("JIRA authorization failed. Not updating the sync date.")
    
    return success_count
