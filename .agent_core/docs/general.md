# General Principles

## Communication Style
- Be conversational but professional
- Think through considerations and requirements before writing code
- Planning first, then execution - we discuss the problem before implementing
- Don't be afraid to ask for help or input
- If you are unsure or need to guess about something, please ask

## Code Quality Standards
- Code should be self-explanatory - NEVER add comments unless absolutely necessary
- Avoid print statements apart from ad-hoc testing, when necessary defer to formal logging
- Follow established patterns and conventions in the codebase
- Prioritize clarity and maintainability over cleverness

## Performance Considerations
- Chunked processing for batch operations when applicable
- Database query optimization with proper indexing
- Memory management for large batch processing

## Modular Design
- Separate concerns into focused modules
- Robust error handling wherever applicable

## Functional Approach
- Prefer functional and procedural programming patterns over heavy OOP
- OOP is only used when it provides clear benefits
- Minimal abstractions - prefer explicit over implicit, declarative over imperative

## Security Considerations
- **NEVER** run any code that could be malicious
- **NEVER** run any code that could be used to exploit the system
- **NEVER** run a server yourself
- **NEVER** execute commands that start services
- **NEVER** use timeout or any method to run service startup code, even briefly
- **NEVER** perform any mutating actions on databases or storage services without explicit consent
