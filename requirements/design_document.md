# JiraLicznik Design Document

## Architecture Overview

JiraLicznik follows a service-oriented architecture with clear separation of concerns. The application is organized into the following layers:

### 1. Core Service Layer
- `JiraService`: Central component for Jira API interaction
- Handles authentication, connection, and basic Jira operations
- Abstracts the complexity of the Jira API

### 2. Specialized Service Layers
- `UpdatedIssuesReport`: Handles reporting of issues updated within a date range
- `UserOpenedTasks`: Manages tasks opened by specific users
- `EpicOpenedReport`: Provides reporting on open epics

### 3. Utility Layer
- `utils.py`: Common utility functions (date calculations, formatting, etc.)
- `config.py`: Configuration management and credential handling

### 4. User Interface Layer
- Command-line interfaces for different reporting needs
- Main scripts that can be invoked directly

## Design Patterns

### 1. Service Pattern
The application uses the service pattern to encapsulate business logic and external API interactions. Each service class has a single responsibility and provides a clean API for other components.

### 2. Factory Pattern
Connection handling uses aspects of the factory pattern, creating and managing Jira client instances.

### 3. Facade Pattern
The `JiraService` class acts as a facade, providing a simplified interface to the complex Jira API.

## Data Flow

1. User invokes a specific report script
2. The script initializes the appropriate service
3. The service connects to Jira through `JiraService`
4. Data is retrieved, processed, and transformed
5. Results are presented to the user

## Key Components

### JiraService
- Core component for Jira interaction
- Handles connection, authentication, and field mapping
- Provides methods for issue retrieval and searching

### UpdatedIssuesReport
- Retrieves issues updated within a date range
- Groups issues by project
- Formats data for reporting

### UserOpenedTasks
- Finds tasks opened by specific users
- Filters by date ranges and statuses
- Calculates and displays days spent in current status based on statusDateChanged field
- Provides time-based analysis of issue progression

### Configuration Management
- Secure credential handling
- Environment-based configuration
- Support for custom field mappings

## Error Handling Strategy

1. **Layered Approach**:
   - Low-level errors are caught and transformed into meaningful application errors
   - Higher-level components handle user-facing error messages

2. **Detailed Logging**:
   - Debug-level logs for detailed troubleshooting
   - Info-level logs for operation tracking
   - Error-level logs for issues requiring attention

3. **Graceful Degradation**:
   - Application handles partial failures where possible
   - Clear communication when operations cannot proceed

## Security Considerations

1. **Credential Management**:
   - No hardcoded credentials
   - Support for environment variables
   - Optional config file with appropriate permissions

2. **Data Protection**:
   - Careful handling of sensitive Jira data
   - No unnecessary data retention
   - Proper error message sanitization

## Future Enhancements

1. **Web Interface**:
   - Potential to add a web frontend
   - API layer for service access

2. **Expanded Reporting**:
   - Additional report types
   - Custom report generation

3. **Automation Integration**:
   - Scheduled report generation
   - Integration with notification systems