import pyodbc
import logging
from datetime import datetime
from config import DB_CONNECTION_STRING
from jiraservice import JiraService

logger = logging.getLogger(__name__)

class JiraDBPopulator:
    """
    Handles populating the JIRA data warehouse database with data from the JIRA API.
    Connects to the database and uses stored procedures to insert/update data.
    """
    
    def __init__(self, agent_name="JiraETLAgent"):
        """
        Initialize the database populator.
        
        Args:
            agent_name: Identifier for this ETL agent in the Parameters table
        """
        self.agent_name = agent_name
        self.jira_service = JiraService()
        self.conn = None
        
    def connect(self):
        """Establishes a connection to the database."""
        try:
            self.conn = pyodbc.connect(DB_CONNECTION_STRING)
            logger.info("Connected to the database")
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            raise
    
    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_last_sync_date(self):
        """
        Gets the last date when data was fetched from JIRA API.
        
        Returns:
            datetime: The date of the last sync, or None if no previous sync
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("{CALL warehouse.GetETLParameters(?)}", (self.agent_name,))
            row = cursor.fetchone()
            
            if row:
                # Return the ReadApiDateTo value
                return row.ReadApiDateTo
            else:
                # If no parameters found, try to get the last imported issue date
                cursor.execute("{CALL warehouse.GetLastImportedIssueDate}")
                row = cursor.fetchone()
                
                if row and row[0]:
                    return row[0]
                
                # If still no date, return None
                return None
                
        except Exception as e:
            logger.error(f"Error getting last sync date: {e}")
            return None
    
    def update_sync_date(self, sync_date):
        """
        Updates the last sync date in the database.
        
        Args:
            sync_date: The datetime to save as the last sync date
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("{CALL warehouse.UpdateETLParameters(?, ?)}", 
                           (self.agent_name, sync_date))
            self.conn.commit()
            logger.info(f"Updated last sync date to {sync_date}")
        except Exception as e:
            logger.error(f"Error updating sync date: {e}")
            self.conn.rollback()
    
    def insert_issue_history(self, history_record):
        """
        Inserts an issue history record into the database.
        
        Args:
            history_record: Dictionary containing the issue history data
        """
        try:
            cursor = self.conn.cursor()
            
            # Extract parameters from the history record
            history_id = history_record['historyId']
            history_date = history_record['historyDate']
            fact_type = history_record['factType']
            issue_id = history_record['issueId']
            issue_key = history_record['issueKey']
            issue_type = history_record['typeName']
            status = history_record['statusName']
            
            # Optional fields that might be None
            assignee_username = history_record.get('assigneeUserName')
            assignee_display = history_record.get('assigneeDisplayName')
            reporter_username = history_record.get('reporterUserName')
            reporter_display = history_record.get('reporterDisplayName')
            allocation_code = history_record.get('allocationCode')
            project_key = history_record['projectKey']
            project_name = history_record['projectName']
            parent_key = history_record.get('parentKey')
            author_username = history_record['authorUserName']
            author_display = history_record.get('authorDisplayName')
            
            # Call the stored procedure to insert the record
            cursor.execute(
                "{CALL warehouse.InsertIssueHistory(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}",
                (history_id, history_date, fact_type, issue_id, issue_key, issue_type, status,
                 assignee_username, assignee_display, reporter_username, reporter_display,
                 allocation_code, project_key, project_name, parent_key,
                 author_username, author_display)
            )
            self.conn.commit()
            logger.debug(f"Inserted history record for {issue_key} with ID {history_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting issue history: {e}")
            self.conn.rollback()
            return False
    
    def populate_from_jira(self, start_date=None, end_date=None, max_issues=None):
        """
        Fetches data from JIRA and populates the database.
        
        Args:
            start_date: The date to start fetching from (default: last sync date)
            end_date: The date to fetch up to (default: now)
            max_issues: Maximum number of issues to process (default: no limit)
            
        Returns:
            int: Number of records successfully inserted
        """
        if not self.conn:
            self.connect()
        
        # If no start_date provided, get the last sync date
        if not start_date:
            start_date = self.get_last_sync_date()
        
        # If no end_date provided, use current time
        if not end_date:
            end_date = datetime.now()
            
        logger.info(f"Populating database with JIRA data from {start_date} to {end_date}")
        
        # Get issue history records from JIRA
        history_records = self.jira_service.get_issue_history(start_date, end_date, max_issues)
        
        # Process each history record
        success_count = 0
        for record in history_records:
            if self.insert_issue_history(record):
                success_count += 1
                
        # Update the last sync date
        self.update_sync_date(end_date)
        
        logger.info(f"Successfully inserted {success_count} out of {len(history_records)} records")
        return success_count

    def get_database_summary(self, days=30):
        """
        Gets a summary of the data in the database.
        
        Args:
            days: Number of days to include in the summary (default: 30)
            
        Returns:
            dict: Summary statistics about the database
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("{CALL warehouse.GetIssueHistorySummary(?, ?)}", 
                          (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - 
                           datetime.timedelta(days=days), None))
            row = cursor.fetchone()
            
            if row:
                return {
                    'total_records': row.TotalRecords,
                    'oldest_record': row.OldestRecord,
                    'newest_record': row.NewestRecord,
                    'unique_issues': row.UniqueIssues,
                    'unique_projects': row.UniqueProjects
                }
            else:
                return {
                    'total_records': 0,
                    'oldest_record': None,
                    'newest_record': None,
                    'unique_issues': 0,
                    'unique_projects': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return None
            
# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("jira_etl.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create and use the populator
    populator = JiraDBPopulator()
    try:
        populator.connect()
        
        # Populate with the last 7 days of data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        count = populator.populate_from_jira(start_date, end_date)
        print(f"Inserted {count} records")
        
        # Get and print a summary
        summary = populator.get_database_summary()
        if summary:
            print(f"Database Summary:")
            print(f"Total Records: {summary['total_records']}")
            print(f"Date Range: {summary['oldest_record']} to {summary['newest_record']}")
            print(f"Unique Issues: {summary['unique_issues']}")
            print(f"Unique Projects: {summary['unique_projects']}")
            
    finally:
        populator.close()