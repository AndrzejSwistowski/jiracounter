"""
Test module for IssueHistoryExtractor.

This module contains tests to verify the functionality of the IssueHistoryExtractor class.
"""

import unittest
from unittest.mock import Mock, MagicMock
from issue_history_extractor import IssueHistoryExtractor
from issue_data_extractor import IssueDataExtractor
from jira_field_manager import JiraFieldManager
import logging

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestIssueHistoryExtractor(unittest.TestCase):
    """Test cases for IssueHistoryExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.field_manager = Mock(spec=JiraFieldManager)
        self.data_extractor = Mock(spec=IssueDataExtractor)
        self.extractor = IssueHistoryExtractor(self.field_manager, self.data_extractor)

    def test_initialization(self):
        """Test that the extractor initializes correctly."""
        self.assertEqual(self.extractor.field_manager, self.field_manager)
        self.assertEqual(self.extractor.data_extractor, self.data_extractor)
        self.assertIsNotNone(self.extractor.logger)

    def test_extract_description_with_valid_description(self):
        """Test description extraction with a valid description."""
        # Create mock issue with description
        issue = Mock()
        issue.fields = Mock()
        issue.fields.description = "This is a test description"
        
        result = self.extractor._extract_description(issue, "TEST-123")
        
        self.assertEqual(result, "This is a test description")

    def test_extract_description_with_no_description(self):
        """Test description extraction when no description exists."""
        # Create mock issue without description
        issue = Mock()
        issue.fields = Mock()
        issue.fields.description = None
        
        result = self.extractor._extract_description(issue, "TEST-123")
        
        self.assertIsNone(result)

    def test_extract_comments_with_valid_comments(self):
        """Test comment extraction with valid comments."""
        # Create mock issue with comments
        issue = Mock()
        issue.fields = Mock()
        issue.fields.comment = Mock()
        
        comment1 = Mock()
        comment1.body = "First comment"
        comment1.created = "2023-01-01T10:00:00+00:00"
        comment1.author = Mock()
        comment1.author.displayName = "John Doe"
        
        comment2 = Mock()
        comment2.body = "Second comment"
        comment2.created = "2023-01-02T11:00:00+00:00"
        comment2.author = Mock()
        comment2.author.displayName = "Jane Smith"
        
        issue.fields.comment.comments = [comment1, comment2]
        
        result = self.extractor._extract_comments(issue, "TEST-123")
        
        self.assertIsNotNone(result)
        self.assertIn("First comment", result)
        self.assertIn("Second comment", result)
        self.assertIn("John Doe", result)
        self.assertIn("Jane Smith", result)

    def test_extract_comments_with_no_comments(self):
        """Test comment extraction when no comments exist."""
        # Create mock issue without comments
        issue = Mock()
        issue.fields = Mock()
        issue.fields.comment = Mock()
        issue.fields.comment.comments = []
        
        result = self.extractor._extract_comments(issue, "TEST-123")
        
        self.assertIsNone(result)

    def test_create_creation_record(self):
        """Test creation of issue creation record."""
        # Mock issue data
        issue = Mock()
        issue.id = "12345"
        issue.fields = Mock()
        issue.fields.project = Mock()
        issue.fields.project.key = "TEST"
        issue.fields.project.name = "Test Project"
        
        issue_data = {
            'created': '2023-01-01T10:00:00+00:00',
            'type': 'Story',
            'assignee': 'jdoe',
            'reporter': 'jsmith',
            'allocation_code': 'NEW',
            'summary': 'Test Issue',
            'labels': ['test'],
            'components': [],
            'parent_issue': None,
            'epic_issue': None,
            'status_change_date': None,
            'updated': '2023-01-01T10:00:00+00:00'
        }
        
        description_text = "Test description"
        comment_text = "Test comments"
        
        result = self.extractor._create_creation_record(
            issue, "TEST-123", issue_data, description_text, comment_text
        )
        
        # Verify the creation record structure
        self.assertEqual(result['factType'], 1)  # 1 = create
        self.assertEqual(result['issueKey'], "TEST-123")
        self.assertEqual(result['typeName'], 'Story')
        self.assertEqual(result['statusName'], 'Open')
        self.assertEqual(result['allocationCode'], 'NEW')
        self.assertEqual(result['projectKey'], 'TEST')
        self.assertEqual(result['projectName'], 'Test Project')
        self.assertEqual(result['summary'], 'Test Issue')
        self.assertEqual(result['workingDaysFromCreation'], 0)
        self.assertEqual(result['workingDaysInStatus'], 0)
        self.assertEqual(result['description_text'], description_text)
        self.assertEqual(result['comment_text'], comment_text)
        
        # Verify changes include description
        self.assertEqual(len(result['changes']), 1)
        self.assertEqual(result['changes'][0]['field'], 'description')
        self.assertEqual(result['changes'][0]['to'], description_text)

    def test_safe_get_field_delegation(self):
        """Test that safe_get_field properly delegates to field manager."""
        # Set up mock return value
        self.field_manager.safe_get_field.return_value = "test_value"
        
        # Call the method
        result = self.extractor.safe_get_field("test_obj", "test_field", "default")
        
        # Verify delegation
        self.field_manager.safe_get_field.assert_called_once_with("test_obj", "test_field", "default")
        self.assertEqual(result, "test_value")


def run_basic_test():
    """Run a basic functionality test."""
    print("Testing IssueHistoryExtractor basic functionality...")
    
    # Create real instances (not mocks) for basic test
    field_manager = JiraFieldManager()
    data_extractor = IssueDataExtractor(field_manager)
    extractor = IssueHistoryExtractor(field_manager, data_extractor)
    
    print(f"✓ IssueHistoryExtractor created successfully")
    print(f"✓ Field manager: {type(extractor.field_manager).__name__}")
    print(f"✓ Data extractor: {type(extractor.data_extractor).__name__}")
    print(f"✓ Logger: {extractor.logger.name}")
    
    # Test description extraction with mock data
    issue = Mock()
    issue.fields = Mock()
    issue.fields.description = "Test description for extraction"
    
    description = extractor._extract_description(issue, "TEST-123")
    print(f"✓ Description extraction: {description}")
    
    print("\nAll basic tests passed!")


if __name__ == "__main__":
    # Run basic test first
    run_basic_test()
    print("\n" + "="*50 + "\n")
    
    # Run unit tests
    unittest.main(verbosity=2)
