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

# Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria like "make it work" require constant clarification.
