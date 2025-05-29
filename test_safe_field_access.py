import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from jira_field_manager import JiraFieldManager
from issue_data_extractor import IssueDataExtractor

class TestSafeFieldAccess(unittest.TestCase):
    """Tests to verify the refactored code using JiraFieldManager's safe_get_field."""
    
    def setUp(self):
        self.field_manager = JiraFieldManager()
        self.extractor = IssueDataExtractor(self.field_manager)
        
    def test_safe_get_field_dictionary(self):
        """Test safe_get_field with a dictionary object."""
        test_dict = {'key': 'value', 'nested': {'child': 'data'}}
        
        # Test direct access
        self.assertEqual(self.extractor.safe_get_field(test_dict, 'key'), 'value')
        
        # Test missing key
        self.assertIsNone(self.extractor.safe_get_field(test_dict, 'missing_key'))
        
        # Test default value
        self.assertEqual(self.extractor.safe_get_field(test_dict, 'missing_key', 'default'), 'default')
    
    def test_safe_get_field_object(self):
        """Test safe_get_field with an object having attributes."""
        class TestObject:
            def __init__(self):
                self.name = "Test Name"
                self.value = 42
                
        test_obj = TestObject()
        
        # Test direct attribute access
        self.assertEqual(self.extractor.safe_get_field(test_obj, 'name'), 'Test Name')
        self.assertEqual(self.extractor.safe_get_field(test_obj, 'value'), 42)
        
        # Test missing attribute
        self.assertIsNone(self.extractor.safe_get_field(test_obj, 'missing_attr'))
        
    def test_property_holder_simulation(self):
        """Test with an object simulating a PropertyHolder."""
        class PropertyHolder:
            def __init__(self, properties):
                self.__dict__.update(properties)
                
        # Create a simulated issue with parent
        parent = PropertyHolder({
            'id': 'PARENT-1',
            'key': 'PARENT-123',
            'fields': PropertyHolder({
                'summary': 'Parent Issue Summary'
            })
        })
        
        fields = PropertyHolder({
            'summary': 'Test Issue',
            'parent': parent
        })
        
        issue = PropertyHolder({
            'key': 'TEST-123',
            'id': '12345',
            'fields': fields
        })
        
        # Test basic extraction
        self.assertEqual(self.extractor.safe_get_field(issue, 'key'), 'TEST-123')
        
        # Test parent extraction
        parent_field = self.extractor.safe_get_field(fields, 'parent')
        self.assertEqual(self.extractor.safe_get_field(parent_field, 'key'), 'PARENT-123')
        
        # Test nested extraction
        parent_fields = self.extractor.safe_get_field(parent_field, 'fields')
        self.assertEqual(self.extractor.safe_get_field(parent_fields, 'summary'), 'Parent Issue Summary')
        
if __name__ == '__main__':
    unittest.main()
