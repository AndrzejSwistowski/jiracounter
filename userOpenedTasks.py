"""
This module provides functionality to retrieve all open tasks for users from a JIRA server.
It depends on the JiraService and Users classes for retrieving data from JIRA.
"""

import logging
from typing import List, Dict, Any, Optional
from jiraservice import JiraService
from users import Users
import config
from utils import calculate_days_since_date

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

class UserOpenedTasks:
    """Service class to retrieve information about open tasks assigned to users in Jira."""
    
    def __init__(self, jira_service: Optional[JiraService] = None, users_service: Optional[Users] = None):
        """Initialize the UserOpenedTasks service.
        
        Args:
            jira_service: An existing JiraService instance or None to create a new one
            users_service: An existing Users instance or None to create a new one
        """
        self.jira_service = jira_service or JiraService()
        self.users_service = users_service or Users(self.jira_service)
    
    def get_open_tasks_for_user(self, user_account_id: str) -> List[Dict[str, Any]]:
        """Get all open tasks assigned to a specific user.
        
        Args:
            user_account_id: The Jira account ID of the user
            
        Returns:
            List of dictionaries containing task information
        """
        try:
            # JQL query to find all issues assigned to the user that are opencl
            jql = f'type NOT IN ( Epic, Spotkanie ) AND assignee = "{user_account_id}" AND status NOT IN (Backlog, \"TO DO\", \"DO ZROBIENIA\", Done, Canceled, Closed, Completed, Dotarło, Resolved) ORDER BY created DESC'
            
            # Get raw issues data
            raw_tasks = self.jira_service.search_issues(jql)
            
            # Process each task to include additional information
            tasks_with_details = []
            for task in raw_tasks:
                try:
                    # Get the full issue to access all fields
                    issue_key = task["key"]
                    issue_details = self.jira_service.get_issue(issue_key)
                    
                    # Create the task information dictionary
                    task_info = {
                        "key": issue_key,
                        "summary": issue_details["summary"],
                        "status": issue_details["status"],
                        "type": task.get("type", issue_details.get("type", "Unknown")),  # Try to get from task first, then issue_details
                        "created_date": issue_details["created_date"],
                        "days_since_creation": issue_details["days_since_creation"],
                        "reporter": issue_details["reporter"],
                        "assignee": issue_details["assignee"],
                        "backetKey": issue_details.get("backetKey", "Undefined"),  # Default to "Undefined" if not found
                        "status_change_date": issue_details.get("status_change_date", None),
                        "daysInCurrentStatus": calculate_days_since_date(issue_details.get("status_change_date", None)) if issue_details.get("status_change_date") else None
                    }
                    
                    tasks_with_details.append(task_info)
                except Exception as e:
                    logger.warning(f"Error processing task {task.get('key', 'unknown')}: {str(e)}")
                    continue
                
            return tasks_with_details
            
        except ConnectionError as e:
            logger.error(f"Connection error retrieving tasks for user: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving tasks for user: {str(e)}")
            raise
    
    def get_tasks_by_display_name(self, display_name: str) -> List[Dict[str, Any]]:
        """Get all open tasks assigned to a user by their display name.
        
        Args:
            display_name: The display name of the user
            
        Returns:
            List of dictionaries containing task information
        """
        try:
            user = self.users_service.get_user_by_name(display_name)
            if not user:
                logger.warning(f"User not found: {display_name}")
                return []
                
            return self.get_open_tasks_for_user(user["accountId"])
        except Exception as e:
            logger.error(f"Error retrieving tasks for user {display_name}: {str(e)}")
            raise
    
    def get_all_users_open_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all open tasks for all active users.
        
        Returns:
            Dictionary with user display names as keys and lists of tasks as values
        """
        try:
            # Get all active users
            all_users = self.users_service.get_all_users(include_inactive=False)
            
            all_tasks = {}
            
            for user in all_users:
                try:
                    user_tasks = self.get_open_tasks_for_user(user["accountId"])
                    if user_tasks:  # Only include users that have open tasks
                        all_tasks[user["displayName"]] = user_tasks
                except Exception as e:
                    logger.warning(f"Error retrieving tasks for user {user['displayName']}: {str(e)}. Skipping.")
                    
            return all_tasks
        except ConnectionError as e:
            logger.error(f"Connection error retrieving tasks for all users: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving tasks for all users: {str(e)}")
            raise
    
    def get_project_users_open_tasks(self, project_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all open tasks for all users in a specific project.
        
        Args:
            project_key: The Jira project key (e.g., "PROJ")
            
        Returns:
            Dictionary with user display names as keys and lists of tasks as values
        """
        try:
            # Get users associated with the project
            project_users = self.users_service.get_project_users(project_key)
            
            project_tasks = {}
            
            for user in project_users:
                try:
                    user_tasks = self.get_open_tasks_for_user(user["accountId"])
                    if user_tasks:  # Only include users that have open tasks
                        project_tasks[user["displayName"]] = user_tasks
                except Exception as e:
                    logger.warning(f"Error retrieving tasks for user {user['displayName']}: {str(e)}. Skipping.")
                    
            return project_tasks
        except ConnectionError as e:
            logger.error(f"Connection error retrieving tasks for project users: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving tasks for project users: {str(e)}")
            raise

# Usage example
if __name__ == "__main__":
    try:
        user_tasksService = UserOpenedTasks()
        
        # Example: Get tasks for all users
        all_tasks = user_tasksService.get_all_users_open_tasks()
        
        # Display the results
        total_tasks = sum(len(tasks) for tasks in all_tasks.values())
        print(f"Found {total_tasks} open tasks for {len(all_tasks)} users:")
        
        for user_name, user_tasks in all_tasks.items():
            print(f"\nUser: {user_name} - {len(user_tasks)} open tasks:")
            for task in user_tasks:
                status_info = f"({task['status']})"

                if task.get('daysInCurrentStatus') is not None:
                    if task.get('daysInCurrentStatus') == 0:
                        status_info = f"({task['status']} - since today)"
                    else:
                        status_info = f"({task['status']} - {task['daysInCurrentStatus']} days)"
                
                print(f"  {task['key']}: [{task['type']}] {task['summary']} {status_info} - "
                      f"Created {task['created_date']} ({task['days_since_creation']} days ago): [{task['backetKey']}] ")
                
        # If command line arguments are provided, use them to get tasks for a specific user
        import sys
        if len(sys.argv) > 1:
            user_name = sys.argv[1]
            print(f"\n\nLooking up tasks for user: {user_name}")
            user_specific_tasks = user_tasksService.get_tasks_by_display_name(user_name)
            print(f"Found {len(user_specific_tasks)} open tasks for {user_name}:")
            for task in user_specific_tasks:
                status_info = f"({task['status']})"
                if task.get('daysInCurrentStatus') is not None:
                    if task.get('daysInCurrentStatus') == 0:
                        status_info = f"({task['status']} - since today)"
                    else:
                        status_info = f"({task['status']} - {task['daysInCurrentStatus']} days)"
                
                print(f"  {task['key']}: TaskType:[{task['type']}|'Unknown'] {task['summary']} {status_info} - "
                      f"Created {task['created_date']} ({task['days_since_creation']} days ago) [{task['backetKey']}]")
                
    except Exception as e:
        print(f"Error: {str(e)}")
