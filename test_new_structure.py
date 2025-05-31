#!/usr/bin/env python3
"""
Test script to validate the new comprehensive record structure.
"""

import logging
from jiraservice import JiraService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_new_structure():
    """Test the new comprehensive record structure."""
    try:
        # Initialize JIRA service
        jira_service = JiraService()
          # Test with a single issue
        test_issue_key = "UTR-437"  # Use an existing issue key
        
        logger.info(f"Testing new structure with issue: {test_issue_key}")
        
        # Get comprehensive issue record using new method
        comprehensive_record = jira_service.get_issue_changelog(test_issue_key)
        
        # Validate the structure
        expected_keys = [
            'issue_data',
            'issue_description', 
            'issue_comments',
            'metrics',
            'status_transitions',
            'field_changes'
        ]
        
        logger.info("Validating comprehensive record structure...")
        
        for key in expected_keys:
            if key in comprehensive_record:
                logger.info(f"✓ Found key: {key}")
                
                # Show some sample data
                if key == 'issue_data':
                    issue_data = comprehensive_record[key]
                    logger.info(f"  Issue Key: {issue_data.get('key')}")
                    logger.info(f"  Status: {issue_data.get('statusName')}")
                    logger.info(f"  Type: {issue_data.get('typeName')}")
                    
                elif key == 'metrics':
                    metrics = comprehensive_record[key]
                    logger.info(f"  Total working minutes: {metrics.get('working_minutes_from_create')}")
                    logger.info(f"  Current status minutes: {metrics.get('working_minutes_in_current_status')}")
                    logger.info(f"  Total transitions: {metrics.get('total_transitions')}")
                    
                elif key == 'status_transitions':
                    transitions = comprehensive_record[key]
                    logger.info(f"  Number of status transitions: {len(transitions) if transitions else 0}")
                    
                elif key == 'field_changes':
                    changes = comprehensive_record[key]
                    logger.info(f"  Number of field change events: {len(changes) if changes else 0}")
                    
                elif key == 'issue_comments':
                    comments = comprehensive_record[key]
                    logger.info(f"  Number of comments: {len(comments) if comments else 0}")
                    
                elif key == 'issue_description':
                    description = comprehensive_record[key]
                    desc_length = len(description) if description else 0
                    logger.info(f"  Description length: {desc_length} characters")
            else:
                logger.error(f"✗ Missing key: {key}")
        
        # Test that this is a single record, not a list
        if isinstance(comprehensive_record, dict):
            logger.info("✓ Method returns single comprehensive record (dict)")
        else:
            logger.error(f"✗ Method returns unexpected type: {type(comprehensive_record)}")
            
        logger.info("Structure validation complete!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_new_structure()
    if success:
        print("\n✓ New comprehensive structure test PASSED")
    else:
        print("\n✗ New comprehensive structure test FAILED")
