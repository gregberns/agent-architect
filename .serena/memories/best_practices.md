# Agent Architect Development Best Practices

## Project Structure
- Create language-specific modules in isolated directories for future expansion
- Use `src/io/` for OS/filesystem operations 
- Use `src/analysis/` for language analysis modules
- Maintain clear separation between core logic and external integrations

## Code Organization
- Follow "Functional Core, Imperative Shell" pattern
- Use services/interfaces for external dependencies (git, databases, APIs)
- Keep modules focused on single responsibilities
- Design for testability from the start

## Testing Standards
- Aim for 100% test coverage on core business logic
- Test error conditions and edge cases thoroughly
- Use property-based testing where appropriate
- Create integration tests for external tool interactions

## Documentation Requirements
- Document module interfaces clearly
- Include usage examples in module documentation
- Document design decisions and architectural patterns
- Keep README files updated with setup and usage instructions

## ReasonML/OCaml Specific
- Use meaningful type names and leverage the type system
- Prefer explicit error handling with Result types
- Use consistent naming conventions across modules
- Leverage pattern matching for robust error handling

## External Tool Integration
- Always handle subprocess failures gracefully
- Provide clear error messages for missing dependencies
- Design interfaces that can be easily mocked for testing
- Consider cross-platform compatibility (Windows, macOS, Linux)