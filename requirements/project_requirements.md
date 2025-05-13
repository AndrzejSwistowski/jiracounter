# JiraCounter Project Requirements

## Overview
JiraCounter is a Python application designed to interact with Jira API to retrieve and process issue information for reporting and tracking purposes.

## Functional Requirements

### 1. Jira Connection
- The system must securely connect to a Jira instance using API tokens
- The system must handle connection errors gracefully
- Credentials must be stored securely and not hardcoded

### 2. Issue Retrieval
- Retrieve complete issue details by issue key
- Support custom fields, particularly 'rodzaj pracy' field
- Support custom field 'data zmiany statusu' for tracking status change dates and time - the value must be passed with the time
- Extract and format date and time information for reporting in format YYYY-MM-dd HH:mm:ss
- Calculate time-based metrics such as days since creation

### 3. Issue Searching
- Support JQL queries to search for issues
- Implement pagination to handle large result sets
- Limit results to a reasonable maximum (1000 by default)

### 4. Reporting
- Generate reports of issues updated within a date range
- Group issues by project
- Sort issues by relevant criteria (e.g., update date)
- Calculate and display appropriate metrics

### 5. User Interactions
- Provide clear command-line interfaces for all functionality
- Display appropriate error messages
- Format output for easy reading and interpretation

## Technical Requirements

### 1. Code Architecture
- Follow object-oriented design principles
- Implement service layer architecture with separation of concerns
- Use appropriate design patterns where beneficial

### 2. Error Handling
- Implement comprehensive error handling
- Log errors with appropriate severity levels
- Provide user-friendly error messages

### 3. Performance
- Optimize API calls to minimize latency
- Implement pagination for large result sets
- Cache frequently used data when appropriate

### 4. Security
- Store credentials securely
- Support API token authentication
- Never log sensitive information

### 5. Testing
- Implement unit tests for core functionality
- Mock external dependencies for testing
- Achieve high test coverage for critical components

### 6. Documentation
- Document all modules, classes, and functions
- Provide usage examples
- Include installation and setup instructions

### 7. Code Quality
- Follow established coding principles including DRY (Don't Repeat Yourself)
- Apply Tell Don't Ask principle to ensure proper encapsulation
- Organize code with implementation functions below the functions that call them
- Include comprehensive docstrings for all modules, classes, and functions
- Implement appropriate error handling with meaningful error messages
- Write unit tests for core functionality with at least 70% code coverage

## Dependencies
Required Python packages are specified in the `requirements.txt` file and include:
- jira - For Jira API integration
- python-dateutil - For date manipulation
- pytest - For testing

## Installation
Installation instructions should include:
1. Clone the repository
2. Install dependencies from requirements.txt
3. Configure credentials
4. Run test suite to verify setup