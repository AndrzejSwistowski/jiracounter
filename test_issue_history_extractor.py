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
        
        # Verify the result is a list with correct structure
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        
        # Check first comment
        comment1_result = result[0]
        self.assertEqual(comment1_result['body'], "First comment")
        self.assertEqual(comment1_result['author'], "John Doe")
        self.assertEqual(comment1_result['created_at'], "2023-01-01T10:00:00+00:00")
        
        # Check second comment
        comment2_result = result[1]
        self.assertEqual(comment2_result['body'], "Second comment")
        self.assertEqual(comment2_result['author'], "Jane Smith")
        self.assertEqual(comment2_result['created_at'], "2023-01-02T11:00:00+00:00")

    def test_extract_comments_with_no_comments(self):
        """Test comment extraction when no comments exist."""
        # Create mock issue without comments
        issue = Mock()
        issue.fields = Mock()
        issue.fields.comment = Mock()
        issue.fields.comment.comments = []
        result = self.extractor._extract_comments(issue, "TEST-123")
        self.assertIsNone(result)

    def test_field_manager_integration(self):
        """Test that extractor properly uses field manager through data extractor."""
        # Set up mock issue data extraction
        self.data_extractor.extract_issue_data.return_value = {
            'key': 'TEST-123',
            'summary': 'Test Issue',
            'status': 'Open'
        }
        
        # Create a mock issue with proper changelog structure
        issue = Mock()
        issue.fields = Mock()
        issue.fields.description = "Test description"
        issue.fields.comment = Mock()
        issue.fields.comment.comments = []
        
        # Mock changelog structure to avoid iteration error
        issue.changelog = Mock()
        issue.changelog.histories = []  # Empty list instead of Mock
        
        # Test that extract_issue_changelog uses the data extractor
        result = self.extractor.extract_issue_changelog(issue, "TEST-123")
        
        # Verify that data extractor was called
        self.data_extractor.extract_issue_data.assert_called_once_with(issue)
        
        # Verify the structure of the result
        self.assertIsInstance(result, dict)
        self.assertIn('issue_data', result)
        self.assertIn('issue_description', result)
        self.assertIn('issue_comments', result)
        self.assertIn('metrics', result)
        self.assertIn('status_transitions', result)
        self.assertIn('field_changes', result)


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
