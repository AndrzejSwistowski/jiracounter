#!/usr/bin/env python3
"""
Test script to verify duplicate detection functionality in bulk_insert_issue_history.
"""

import sys
import os
import logging
from datetime import datetime, timezone
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from es_populate import JiraElasticsearchPopulator
from config import ES_HOST, ES_PORT
from logger_utils import setup_logging

# Set up logging
logger = setup_logging(__name__, verbose=True, log_to_file=False)

def create_test_record(issue_key, timestamp_str):
    """Create a test issue record with the specified timestamp."""
    return {
        'issue_data': {
            'id': '12345',  # Use 'id' instead of 'issueId'
            'key': issue_key,
            'summary': f'Test issue {issue_key}',
            'status': 'To Do',  # Use string status instead of dict
            'type': 'Task',  # Use string type instead of dict
            'priority': 'Medium',  # Use string priority instead of dict
            'created': timestamp_str,
            'updated': timestamp_str,
            'assignee': {'display_name': 'Test User'},
            'reporter': {'display_name': 'Test Reporter'},
            'project': {'key': 'TEST', 'name': 'Test Project'},
        },
        'issue_description': 'Test issue description',
        'issue_comments': [],
        'metrics': {
            'working_minutes_from_create': 100,
            'working_minutes_in_current_status': 50,
            'working_minutes_from_first_move': 75,
            'backlog_minutes': 0,
            'processing_minutes': 100,
            'waiting_minutes': 0,
            'total_transitions': 1,
            'backflow_count': 0,
            'unique_statuses_visited': ['To Do'],
            'status_change_date': timestamp_str
        },
        'status_transitions': [
            {
                'from_status': None,
                'to_status': 'To Do',
                'transition_date': timestamp_str,
                'minutes_in_previous_status': 0,
                'is_forward_transition': True,
                'is_backflow': False,
                'author': 'Test User'
            }
        ],
        'field_changes': []
    }

def test_duplicate_detection():
    """Test that duplicate detection works correctly."""
    logger.info("Starting duplicate detection test...")
    
    try:
        # Initialize the populator
        populator = JiraElasticsearchPopulator()
        populator.connect()
        
        # Test data
        test_timestamp = "2024-01-01T10:00:00Z"
        test_issue_key = "DUPTEST-001"
        
        # Create identical test records
        record1 = create_test_record(test_issue_key, test_timestamp)
        record2 = create_test_record(test_issue_key, test_timestamp)  # Exact duplicate
        
        logger.info("Testing first insertion (should succeed)...")
        
        # First insertion should work
        result1 = populator.bulk_insert_issue_history([record1])
        logger.info(f"First insertion result: {result1} records inserted")
        
        if result1 != 1:
            logger.error("First insertion should have inserted 1 record")
            return False
        
        logger.info("Testing duplicate insertion (should be skipped)...")
        
        # Second insertion should be skipped due to duplicate detection
        result2 = populator.bulk_insert_issue_history([record2])
        logger.info(f"Duplicate insertion result: {result2} records inserted")
        
        if result2 != 0:
            logger.error("Duplicate insertion should have inserted 0 records")
            return False
        
        logger.info("Testing force override (should succeed)...")
        
        # Third insertion with force override should work
        result3 = populator.bulk_insert_issue_history([record2], force_override=True)
        logger.info(f"Force override result: {result3} records inserted")
        
        if result3 != 1:
            logger.error("Force override should have inserted 1 record")
            return False
        
        logger.info("All duplicate detection tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error during duplicate detection test: {e}")
        return False

def cleanup_test_data():
    """Clean up test data from Elasticsearch."""
    logger.info("Cleaning up test data...")
    
    try:
        populator = JiraElasticsearchPopulator()
        populator.connect()
        
        # Delete test documents
        import requests
        
        # Search for test documents
        query = {
            "query": {
                "term": {
                    "issue_key": "DUPTEST-001"
                }
            }
        }
        
        response = requests.post(f"{populator.base_url}/jira-changelog/_search", 
                               headers=populator.headers, json=query, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            hits = result.get('hits', {}).get('hits', [])
            
            for hit in hits:
                doc_id = hit['_id']
                delete_response = requests.delete(f"{populator.base_url}/jira-changelog/_doc/{doc_id}", 
                                                headers=populator.headers, timeout=10)
                if delete_response.status_code in [200, 404]:
                    logger.info(f"Deleted test document {doc_id}")
                else:
                    logger.warning(f"Failed to delete test document {doc_id}: {delete_response.status_code}")
        
        logger.info("Test data cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def main():
    """Main test function."""
    logger.info("Starting duplicate detection functionality test")
    
    try:
        # Run the test
        success = test_duplicate_detection()
        
        if success:
            logger.info("✅ Duplicate detection test PASSED")
            return_code = 0
        else:
            logger.error("❌ Duplicate detection test FAILED")
            return_code = 1
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return_code = 1
    
    finally:
        # Clean up test data
        cleanup_test_data()
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())
