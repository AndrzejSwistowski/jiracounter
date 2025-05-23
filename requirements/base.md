
## Coding Principles

### SOLID Principles
1. **Single Responsibility Principle** - Each class should have only one reason to change
2. **Open/Closed Principle** - Software entities should be open for extension but closed for modification
3. **Liskov Substitution Principle** - Derived classes must be substitutable for their base classes
4. **Interface Segregation Principle** - Clients should not be forced to depend on methods they do not use
5. **Dependency Inversion Principle** - Depend on abstractions, not concretions

### DRY (Don't Repeat Yourself)
- Avoid code duplication
- Extract common functionality into reusable components
- Use shared libraries and utilities where appropriate

### Command-Query Separation
- Functions should either:
  - Return a result without changing state (Query)
  - Change state without returning a result (Command)
- Avoid functions that do both to improve predictability and testability

### Self-Documenting Code
- Use descriptive names for variables, methods, and classes that clearly express intent
- Write code that is readable and understandable without comments
- Use the source code itself as documentation rather than relying on comments
- Only use comments to explain "why" something is done, not "what" is being done
- Don't use comments to mark unused code - remove it completely instead, as it can be retrieved from version control if needed
