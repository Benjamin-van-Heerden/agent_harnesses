# Testing Philosophy
Testing is critical to maintaining software quality, but not all tests are created equal. Focus on testing meaningful functionality that could actually break and impact the application.

### Test Structure
- Tests live in `tests/` directory with mirrored source structure
- Focus on meaningful functionality that could realistically break
- Avoid "idiot tests" that test framework behavior or trivial logic

### What to Test
- **Business logic**: Complex algorithms, validation rules, data transformations
- **API endpoints**: Request/response handling, authentication, error cases
- **Database operations**: Query correctness, constraint validation, data integrity
- **Integration points**: External API calls, file processing, inter-service communication

### What NOT to Test
- Framework internals 
- Third-party library behavior 
- Trivial getters/setters or simple data transformations
- Implementation details that don't affect public behavior

**Test Quality Principles:**
1. **Clarity Over Quantity** - Fewer, well-focused tests are better than many redundant ones
2. **Test Behavior, Not Implementation** - Focus on what the code does, not how it does it
3. **Meaningful Assertions** - Each test should verify something that could realistically fail
4. **Isolated Tests** - Tests should not depend on each other or external state
5. **Descriptive Names** - Test names should clearly describe what they're validating

**When in Doubt, Ask:**
- "Does this test validate critical business logic or user-facing behavior?"
- "Could this functionality realistically break in the way it is being tested?"

If the answer is no, delete the test and focus on more valuable testing efforts.

Remember: "Whenever I'm about to do something, I think, 'Would an idiot do that?' And if they would, I do not do that thing." - Dwight Schrute

DELETE tests that don't follow these principles. NO 'IDIOT TESTS'!

**NEVER WRITE OR RUN TESTS UNLESS PROMPTED TO OR WE ARE EXPLICITLY WORKING ON TEST CASES.**

**NEVER RUN A FULL TEST SUITE UNLESS SPECIFICALLY ASKED TO. FOCUS ON SPECIFIC TESTS RELATED TO THE FEATURE/FUNCTIONALITY YOU ARE WORKING ON.**

**NEVER RUN TESTS IN A LOOP, RUN, THEN SEEK FEEDBACK**
