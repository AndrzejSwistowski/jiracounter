# Refactoring Progress Tracking to Follow SOLID Principles

## Problem Analysis

The original `log_progress` function in `populate_es.py` had several issues:

1. **Violation of Single Responsibility Principle (SRP)**
   - It was handling multiple concerns: time tracking, progress calculation, rate calculation, and logging
   - It used global variables (`progress_count` and `start_time`) for state management

2. **Poor Dependency Management**
   - Direct dependency on the global state without proper encapsulation
   - Logger passed as parameter but not used consistently

3. **Limited Extensibility (Violation of Open/Closed Principle)**
   - To add new functionality (like reporting to a different output), the function would need to be modified

4. **Unused Code**
   - The function was defined but not actually used in the ETL process

## Solution Approach

We've created a new `ProgressTracker` class that follows SOLID principles:

### 1. Single Responsibility Principle
- The `ProgressTracker` class has a clear responsibility: tracking progress of long-running operations
- It encapsulates all state related to progress tracking

### 2. Open/Closed Principle
- The class can be extended without modifying existing code
- New output formats or calculators could be added through subclassing

### 3. Liskov Substitution Principle
- The class has a clear interface that subclasses can implement
- The legacy `log_progress` function now delegates to this class

### 4. Interface Segregation Principle
- The API is small and focused
- Only the needed methods are exposed

### 5. Dependency Inversion Principle
- The class depends on abstractions (like a logger interface) rather than concrete implementations
- Dependencies are injected in the constructor

## Implementation Details

### 1. New `ProgressTracker` Class
- Encapsulates progress state
- Provides methods to update and report progress
- Calculates metrics like rate and estimated time remaining
- Has clear separation of responsibilities

### 2. Integration with `JiraElasticsearchPopulator`
- Each populator instance has its own progress tracker
- Progress updates occur after each batch of records is processed
- Final summary is logged after completion

### 3. Backward Compatibility
- The original `log_progress` function is maintained for backward compatibility
- It delegates to a singleton `ProgressTracker` instance

## Benefits of the New Design

1. **Better Code Organization**
   - Progress tracking logic is now isolated in a dedicated class
   - Each component has a clear responsibility

2. **Improved Testability**
   - The `ProgressTracker` class can be tested independently
   - Mock loggers can be injected for testing

3. **Enhanced Reusability**
   - The `ProgressTracker` class can be used by any long-running process
   - It's not tied to specific ETL operations

4. **Proper Encapsulation**
   - Progress state is encapsulated within class instances
   - No more global variables

5. **Better Progress Reporting**
   - More consistent reporting of progress
   - Additional metrics like average processing rate

## How to Use the New Design

```python
# Create a progress tracker
tracker = ProgressTracker(logger=my_logger, name="my_process")

# Reset the tracker at the start of an operation
tracker.reset()

# Update progress during processing
for item in items_to_process:
    process_item(item)
    tracker.update(increment=1, total=len(items_to_process))

# Get metrics
rate = tracker.items_per_second
elapsed = tracker.elapsed_seconds
```

This refactoring demonstrates SOLID principles in action and provides a more maintainable and reusable approach to progress tracking.
