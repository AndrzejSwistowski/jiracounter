"""
This module provides functionality to retrieve and work with users from a JIRA server.
It depends on the JiraService class for authentication and connection to JIRA.
"""
import logging
from typing import List, Dict, Any, Optional
from jiraservice import JiraService
import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class Users:
    """Class for retrieving and managing JIRA users."""
    
    def __init__(self, jira_service: Optional[JiraService] = None):
        """Initialize the Users class.
        
        Args:
            jira_service: An existing JiraService instance or None to create a new one
        """
        self.jira_service = jira_service or JiraService()
        self.jira_client = None
    
    def connect(self):
        """Ensure connection to JIRA server."""
        self.jira_client = self.jira_service.connect()
        return self.jira_client
    
    def get_all_users(self, include_inactive: bool = False, max_results: int = 1000) -> List[Dict[str, Any]]:
        """Get all users from JIRA.
        
        Args:
            include_inactive: Whether to include inactive users
            max_results: Maximum number of users to return
            
        Returns:
            List of user dictionaries containing user details
        """
        jira = self.connect()
        try:
            users = []
            start_at = 0
            
            # JIRA API paginates users, so we need to fetch them in batches
            while True:
                # Use the user_search endpoint with appropriate options
                batch = jira.search_users(
                    user="",
                    query="emailAddress <> ''",
                    maxResults=100,
                    startAt=start_at,
                    includeInactive=include_inactive
                )
                
                if not batch:
                    break
                    
                users.extend(batch)
                
                if len(batch) < 100 or len(users) >= max_results:
                    break
                
                start_at += 100
            
            # Limit to max_results
            users = users[:max_results]
            
            # Convert to a more usable dictionary format
            return [
                {
                    "accountId": user.accountId,
                    "displayName": user.displayName,
                    "emailAddress": getattr(user, "emailAddress", None),
                    "active": user.active,
                    "key": getattr(user, "key", None),
                    "name": getattr(user, "name", None),
                    "self": user.self
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            raise
    
    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a user by display name or username.
        
        Args:
            name: The display name or username to search for
            
        Returns:
            User dictionary if found, None otherwise
        """
        jira = self.connect()
        try:
            results = jira.search_users(query=name)
            for user in results:
                # Try to match on display name or username
                if (user.displayName.lower() == name.lower() or 
                    getattr(user, "name", "").lower() == name.lower()):
                    return {
                        "accountId": user.accountId,
                        "displayName": user.displayName,
                        "emailAddress": getattr(user, "emailAddress", None),
                        "active": user.active,
                        "key": getattr(user, "key", None),
                        "name": getattr(user, "name", None),
                        "self": user.self
                    }
            return None
        except Exception as e:
            logger.error(f"Error finding user {name}: {str(e)}")
            raise
    
    def get_users_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        """Get all users belonging to a specific group.
        
        Args:
            group_name: Name of the group to get users from
            
        Returns:
            List of user dictionaries in the specified group
        """
        jira = self.connect()
        try:
            group_users = []
            start_at = 0
            
            while True:
                # Fetch users in batches
                batch = jira.group_members(group_name, startAt=start_at, maxResults=50)
                
                if not batch.get('values'):
                    break
                    
                group_users.extend(batch['values'])
                
                if batch.get('isLast', True):
                    break
                    
                start_at += 50
            
            # Format the output
            return [
                {
                    "accountId": user.get('accountId'),
                    "displayName": user.get('displayName'),
                    "emailAddress": user.get('emailAddress'),
                    "active": user.get('active'),
                    "name": user.get('name')
                }
                for user in group_users
            ]
        except Exception as e:
            logger.error(f"Error retrieving users from group {group_name}: {str(e)}")
            raise
            
    def get_project_users(self, project_key: str) -> List[Dict[str, Any]]:
        """Get users associated with a specific project.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            
        Returns:
            List of users associated with the project
        """
        jira = self.connect()
        try:
            # Get project roles
            project = jira.project(project_key)
            roles = jira.project_roles(project)
            
            user_dict = {}  # Use dict to avoid duplicates
            
            # Get users for each role
            for role_name, role_url in roles.items():
                role_details = jira.find(role_url)
                if hasattr(role_details, 'actors'):
                    for actor in role_details.actors:
                        if actor.actorType == 'atlassian-user-role-actor':
                            user = actor.displayName
                            user_dict[actor.actorUser.accountId] = {
                                "accountId": actor.actorUser.accountId,
                                "displayName": actor.displayName,
                                "role": role_name,
                                "active": actor.actorUser.active,
                                "name": getattr(actor.actorUser, "name", None)
                            }
            
            return list(user_dict.values())
        except Exception as e:
            logger.error(f"Error retrieving users for project {project_key}: {str(e)}")
            raise


# Example usage
if __name__ == "__main__":
    try:
        user_service = Users()
        
        # Example: Get first 10 users
        all_users = user_service.get_all_users(max_results=10)
        print(f"Found {len(all_users)} users:")
        for user in all_users:
            print(f"- {user['displayName']}")
        
        # Try to get users for a specific project if arguments provided
        import sys
        if len(sys.argv) > 1:
            project_key = sys.argv[1]
            project_users = user_service.get_project_users(project_key)
            print(f"\nUsers for project {project_key}: {len(project_users)}")
            for user in project_users:
                print(f"- {user['displayName']} ({user['role']})")
                
    except Exception as e:
        print(f"Error: {str(e)}")