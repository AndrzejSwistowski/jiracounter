# AI Guidelines for JiraCounter Project

## Project Overview

JiraCounter is a Python application designed to interact with Jira API for retrieving and processing issue information for reporting and tracking purposes. The application uses:

- **Language**: Python 3.x
- **Framework**: Jira API integration using `python-jira`
- **Architecture**: Service-oriented with clear separation of concerns
- **Data Storage**: Elasticsearch for changelog data warehousing
- **Testing**: pytest for unit testing

## Project Architecture

### Core Components

1. **JiraService** - Central component for Jira API interaction
2. **Elasticsearch Integration** - Data warehousing and search capabilities
3. **Reporting Services** - Specialized reporting classes
4. **Utility Layer** - Common functions and date handling
5. **Configuration Management** - Secure credential and settings handling

### Key Patterns Used

- **Service Pattern**: Each service class has single responsibility
- **Factory Pattern**: Connection handling and client creation
- **Facade Pattern**: JiraService simplifies complex Jira API

## Coding Standards and Conventions

### 1. Naming Conventions

```python
# Classes - PascalCase
class JiraService:
class UserOpenedTasks:

# Methods and variables - snake_case
def get_issue_changelog(self):
def search_issues(self):
issue_key = "PROJ-123"
changelog_entries = []

# Constants - UPPER_SNAKE_CASE
JIRA_BASE_URL = "https://company.atlassian.net"
CUSTOM_FIELDS = {...}

# Private methods - leading underscore
def _extract_issue_data(self):
def _extract_backet_info(self):
```

### 2. Function Organization

Follow the principle: **implementation functions below the functions that call them**

```python
class JiraService:
    # Public interface methods first
    def get_issue(self, issue_key: str):
        """Public method using private helper."""
        jira = self.connect()
        issue = jira.issue(issue_key)
        return self._extract_issue_data(issue)
    
    def search_issues(self, jql_query: str):
        """Public search method."""
        # Implementation using helper methods
        pass
    
    # Private helper methods below
    def _extract_issue_data(self, issue):
        """Helper method used by public methods above."""
        pass
```

### 3. Documentation Standards

Use comprehensive docstrings with type hints:

```python
def get_issue_changelog(self, issue_key: str) -> List[Dict[str, Any]]:
    """Retrieve the changelog for a specific issue.
    
    Args:
        issue_key: The Jira issue key (e.g., "PROJ-123")
        
    Returns:
        List of changelog entries containing the history of changes
        
    Raises:
        ConnectionError: If there's an issue connecting to Jira
        ValueError: If issue_key is empty
        Exception: For other errors retrieving the changelog
    """
```

### 4. Error Handling Strategy

```python
# Layered error handling
try:
    issue = jira.issue(issue_key)
    return self._extract_issue_data(issue)
except ConnectionError as e:
    logger.error(f"Connection error retrieving issue {issue_key}: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Error retrieving issue {issue_key}: {str(e)}")
    raise
```

## Working with AI: Best Practices

### 1. Asking Questions About Code

**Good Example:**
```markdown
I'm working on the JiraCounter Python application that uses python-jira library and Elasticsearch. 
I have a performance issue with this LINQ-like query:

```python
# Get all issues updated in last 3 days with full changelog
issues = jira_service.search_issues("updated >= -3d")
for issue in issues:
    changelog = jira_service.get_issue_changelog(issue['key'])
```

How can I optimize this to reduce API calls when I only need status change information?
```

**Context to Always Provide:**
- Python version and key libraries (python-jira, elasticsearch)
- Specific JiraCounter architecture patterns
- Performance or security constraints
- Current error messages or logs

### 2. Code Generation Requests

**Effective Approach:**
```markdown
Please create a new reporting service for JiraCounter that:

Functional Requirements:
- Finds all epics in "In Progress" status for a given project
- Calculates days since epic creation and days in current status
- Returns data compatible with Elasticsearch document format

Technical Requirements:
- Follow existing JiraService pattern
- Use the established error handling approach
- Include comprehensive docstrings
- Follow the project's snake_case naming convention
- Use ISO8601 date formatting (via time_utils.to_iso8601)

Existing Architecture:
- Inherits from or uses JiraService for API calls
- Uses JiraFieldManager for custom field access
- Implements _extract_issue_data pattern for data standardization
```

### 3. Code Review and Refactoring

**Clear Objectives:**
```markdown
Please review this JiraService method for:
- Compliance with project coding standards
- Proper error handling (our pattern: log + re-raise)
- Performance optimization opportunities
- Documentation completeness

Constraints:
- Must maintain backward compatibility with existing callers
- Should follow our established date handling using time_utils
- Keep the service pattern intact
```

## Project-Specific AI Hints

### Custom Field Handling
```python
# AI-HINT: Always use JiraFieldManager for custom field access
# AI-HINT: Custom fields are mapped in config.JIRA_CUSTOM_FIELDS
field_value = self.field_manager.get_field_value(issue, 'rodzaj_pracy')
```

### Date Handling
```python
# AI-HINT: All dates must be in ISO8601 format with timezone
# AI-HINT: Use time_utils functions for date operations
from time_utils import to_iso8601, parse_date, calculate_working_days_between

date_string = to_iso8601(jira_date)
working_days = calculate_working_days_between(start_date, end_date)
```

### Elasticsearch Integration
```python
# AI-HINT: Use ElasticsearchDocumentFormatter for data preparation
# AI-HINT: Follow CHANGELOG_MAPPING structure for document format
formatter = ElasticsearchDocumentFormatter()
document = formatter.format_changelog_entry(changelog_entry)
```

### Error Logging Pattern
```python
# AI-HINT: Use this consistent error logging pattern
try:
    # operation
    pass
except ConnectionError as e:
    logger.error(f"Connection error in {operation_name}: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Error in {operation_name}: {str(e)}")
    raise
```

## Configuration for AI Tools

### Project Metadata
```json
{
  "project": {
    "name": "JiraCounter",
    "description": "Jira API integration for issue tracking and reporting with Elasticsearch warehousing",
    "version": "1.0.0",
    "language": "python",
    "python_version": "3.13+",
    "frameworks": ["python-jira", "elasticsearch", "pytest"],
    "architecture": "service-oriented",
    "data_storage": ["elasticsearch", "local_files"],
    "main_components": [
      "JiraService",
      "JiraFieldManager", 
      "ElasticsearchPopulator",
      "ReportingServices",
      "UtilityLayer"
    ],
    "conventions": {
      "naming": {
        "classes": "PascalCase",
        "methods": "snake_case",
        "variables": "snake_case",
        "constants": "UPPER_SNAKE_CASE",
        "files": "snake_case.py",
        "private_methods": "_snake_case"
      },
      "testing": {
        "framework": "pytest",
        "naming_pattern": "test_{module_name}.py",
        "test_methods": "test_{functionality}",
        "coverage_target": "70%"
      },
      "documentation": {
        "style": "Google",
        "type_hints": "required",
        "docstring_format": "comprehensive",
        "examples": "include_usage_examples"
      },
      "error_handling": {
        "pattern": "log_and_reraise",
        "logging_level": "ERROR",
        "exception_chaining": "preserve_original"
      },
      "imports": {
        "style": "explicit",
        "order": ["standard_library", "third_party", "local"],
        "typing": "required_for_public_methods"
      }
    },
    "directory_structure": {
      "root": "e:\\Zrodla\\jiracounter\\jiracouter",
      "core_modules": [
        "jiraservice.py",
        "config.py", 
        "time_utils.py",
        "jira_field_manager.py"
      ],
      "services": [
        "userOpenedTasks.py",
        "epicOpenedReport.py", 
        "updatedIssues.py"
      ],
      "elasticsearch": [
        "es_populate.py",
        "es_mapping.py",
        "es_document_formatter.py"
      ],
      "utilities": [
        "utils.py",
        "users.py"
      ],
      "tests": [
        "test_jiraservice.py",
        "test_elasticsearch.py"
      ],
      "diagnostic": "diagnostic/",
      "logs": "logs/",
      "data": "data/",
      "requirements": "requirements/"
    },
    "key_dependencies": {
      "jira": "3.x",
      "elasticsearch": "8.x", 
      "python-dateutil": "latest",
      "pytest": "latest"
    },    "environment_variables": {
      "required": [
        "JIRA_API_TOKEN",
        "ELASTIC_URL",
        "ELASTIC_APIKEY"
      ],
      "optional": [
        "JIRA_BASE_URL",
        "JIRA_USERNAME", 
        "JIRA_LOG_LEVEL",
        "JIRA_CACHE_DURATION"
      ]
    },
    "platform": {
      "os": "Windows",
      "shell": "PowerShell",
      "command_syntax": "powershell",
      "forbidden_syntax": ["&&", "||", "bash", "sh"],
      "preferred_patterns": [
        "semicolon_separation",
        "if_lastexitcode_checks",
        "try_catch_blocks"
      ]
    },
    "custom_fields": {
      "RODZAJ_PRACY": "customfield_10138",
      "DATA_ZMIANY_STATUSU": "customfield_10070"
    },
    "design_patterns": [
      "Service Pattern",
      "Factory Pattern", 
      "Facade Pattern",
      "Repository Pattern"
    ],
    "data_formats": {
      "dates": "ISO8601_with_timezone",
      "api_responses": "List[Dict[str, Any]]",
      "elasticsearch_docs": "standardized_mapping"
    }
  }
}
```

### AI Tool Configuration Files

#### .aiconfig (Project Root)
```json
{
  "project_type": "python_jira_integration",
  "primary_contexts": [
    "jira_api_integration",
    "elasticsearch_data_warehousing", 
    "issue_tracking_and_reporting"
  ],
  "code_analysis_hints": {
    "entry_points": [
      "jiraservice.py",
      "populate_es.py",
      "test_jiraservice.py"
    ],
    "critical_paths": [
      "jiraservice.connect()",
      "get_issue_changelog()",
      "search_issues()",
      "elasticsearch_populate()"
    ],
    "data_flow": "jira_api -> jiraservice -> elasticsearch -> reports"
  },
  "common_tasks": [
    "add_new_reporting_service",
    "optimize_jira_api_calls",
    "extend_elasticsearch_mapping",
    "implement_new_field_extraction",
    "create_diagnostic_tools"
  ]
}
```

#### VS Code Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "files.associations": {
    "*.py": "python"
  },
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true
}
```

### Common Patterns

1. **Service Class Structure:**
   ```python
   class SomeService:
       def __init__(self, jira_service=None):
           self.jira_service = jira_service or JiraService()
       
       # Public methods first
       def public_method(self):
           pass
       
       # Private helpers below
       def _private_helper(self):
           pass
   ```

2. **Data Extraction Pattern:**
   ```python
   def _extract_issue_data(self, issue) -> Dict[str, Any]:
       """Extract standardized issue data."""
       return {
           "id": issue.id,
           "key": issue.key,
           "summary": issue.fields.summary,
           # ... standardized fields
       }
   ```

3. **API Response Handling:**
   ```python
   def api_method(self) -> List[Dict[str, Any]]:
       """Always return List[Dict] for consistency."""
       jira = self.jira_service.connect()
       # ... process data
       return standardized_results
   ```

## AI Collaboration Workflow

### 1. Problem Definition
- Clearly state the functional requirement
- Identify which existing patterns to follow
- Specify performance or compatibility constraints

### 2. Implementation
- Request complete methods/classes, not fragments
- Ask for appropriate error handling
- Ensure documentation is included

### 3. Integration
- Verify compatibility with existing architecture
- Check for proper import statements
- Validate error handling patterns

### 4. Testing and Iteration
- Request test cases that follow pytest conventions
- Ask for edge case coverage
- Iterate based on actual runtime behavior

## Security Considerations

### Credential Management
```python
# AI-HINT: Never hardcode credentials
# AI-HINT: Always use config.get_credentials() or environment variables
username, token = config.get_credentials()

# AI-HINT: Use API tokens, not passwords
jira = JIRA(server=config.JIRA_BASE_URL, basic_auth=(username, token))
```

### Data Protection
```python
# AI-HINT: Sanitize sensitive data in logs
logger.debug(f"Processing issue {issue_key}")  # Good
logger.debug(f"Using token {token[:4]}...")    # Good for debugging
logger.debug(f"Full API response: {response}") # Avoid - may contain sensitive data
```

## Performance Guidelines

### API Call Optimization
```python
# AI-HINT: Use pagination for large result sets
# AI-HINT: Cache field IDs to avoid repeated API calls
# AI-HINT: Batch operations when possible

# Good - single search with pagination
issues = self.search_issues(jql_query, max_issues=1000)

# Avoid - multiple individual calls
for issue_key in issue_keys:
    issue = self.get_issue(issue_key)  # N+1 query problem
```

## Windows PowerShell Specific Guidelines

### Command Chaining and Terminal Usage

Since this project runs on Windows with PowerShell, follow these patterns:

```powershell
# CORRECT - PowerShell command chaining
python script.py; if ($LASTEXITCODE -eq 0) { Write-Host "Success" }

# CORRECT - PowerShell conditional execution
if (Test-Path "file.txt") { python process.py }

# INCORRECT - Unix-style (don't use in PowerShell)
python script.py && echo "Success"  # This will cause errors!

# CORRECT - Multiple commands in PowerShell
python script.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "Script completed successfully"
} else {
    Write-Error "Script failed with exit code $LASTEXITCODE"
}
```

### Terminal Command Generation Rules

```powershell
# AI-HINT: Always use PowerShell syntax for terminal commands
# AI-HINT: Use semicolon (;) or separate commands, not && operator
# AI-HINT: Check exit codes with $LASTEXITCODE variable

# Environment variables in PowerShell
$env:ELASTIC_URL = "http://localhost:9200"
[Environment]::SetEnvironmentVariable("ELASTIC_URL", "value", "User")

# File operations
Test-Path "file.txt"           # Check if file exists
Get-Content "file.txt"         # Read file content
Set-Content "file.txt" "data"  # Write to file

# Process management
Start-Process python -ArgumentList "script.py" -NoNewWindow -Wait
```

### Diagnostic Scripts Pattern

Follow the established PowerShell patterns in `/diagnostic/` folder:

```powershell
# Standard error handling for PowerShell scripts
try {
    # Main logic here
    $result = Invoke-SomeOperation
    Write-Host "Operation successful" -ForegroundColor Green
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    # Cleanup code
}
```

## Summary

When working with AI on JiraCounter:

1. **Provide Context**: Always mention Python, Jira API, Elasticsearch context
2. **Follow Patterns**: Use established service patterns and naming conventions  
3. **Document Everything**: Include comprehensive docstrings and type hints
4. **Handle Errors Consistently**: Log and re-raise with context
5. **Test Thoroughly**: Write pytest tests for new functionality
6. **Think Security**: Never expose credentials or sensitive data
7. **Optimize Performance**: Consider API call patterns and caching
8. **Use Windows Syntax**: Always use PowerShell command syntax, never Unix-style `&&` operators
9. **Follow PowerShell Patterns**: Use established patterns from `/diagnostic/` scripts

This ensures AI-generated code integrates seamlessly with the existing JiraCounter architecture and maintains high code quality standards.
