# Coding Principles for JiraLicznik

This document outlines the coding principles and standards to be followed by all contributors to the JiraLicznik project.

## Code Organization

1. **Public Functions First**: Place the most important public functions at the top of classes, with implementation details at the bottom.
2. **Modular Design**: Each module should have a single responsibility.
3. **Class Structure**:
   - Constructor (`__init__`) should always be at the top
   - Public methods should come next, ordered by importance
   - Private methods (prefixed with `_`) should be at the bottom

## Naming Conventions

1. **Variables and Functions**: Use snake_case for variable and function names.
2. **Classes**: Use PascalCase for class names.
3. **Constants**: Use UPPER_CASE for constants.
4. **Private Methods/Attributes**: Prefix private methods and attributes with a single underscore (`_`).

## Documentation

1. **Docstrings**: All modules, classes, and functions must have docstrings.
2. **Function Documentation**: Include:
   - A brief description
   - Args section with parameter descriptions
   - Returns section with return value description
   - Raises section if applicable

Example:
```python
def get_issue(self, issue_key: str) -> Dict[str, Any]:
    """Retrieve an issue by its key.
    
    Args:
        issue_key: The Jira issue key (e.g., "PROJ-123")
        
    Returns:
        Dict containing the issue details
        
    Raises:
        ConnectionError: If there's an issue connecting to Jira
        Exception: For other errors retrieving the issue
    """
```

## Error Handling

1. **Proper Exception Types**: Use appropriate exception types for different error scenarios.
2. **Logging**: Log errors with appropriate severity levels.
3. **User Feedback**: Provide meaningful error messages to users.

## Type Annotations

1. **Type Hints**: Use type hints for function parameters and return values.
2. **Complex Types**: Use the `typing` module for complex types (Dict, List, Optional, etc.).

## Testing

1. **Test Coverage**: Aim for high test coverage of core functionality.
2. **Test Organization**: Each module should have a corresponding test module.
3. **Test Naming**: Test functions should be named descriptively to indicate what they're testing.

## Code Style

1. **PEP 8**: Follow PEP 8 style guidelines.
2. **Line Length**: Keep lines to a maximum of 100 characters.
3. **Imports**: Organize imports in the following order:
   - Standard library imports
   - Third-party imports
   - Local application imports

## Version Control

1. **Commit Messages**: Write clear, descriptive commit messages.
2. **Feature Branches**: Develop new features in separate branches.
3. **Code Reviews**: All code should be reviewed before merging.