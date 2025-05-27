# Test Commands

## Running Tests
- `yarn run jest` - Run all Jest tests in the project
- This is the primary command for executing the test suite

## Test File Naming Convention
- Test files must end with `_Tests.re` (not `_test.re`)
- Example: `FileSystem_Tests.re`, `CodebaseDiscovery_Tests.re`

## Module References in Tests
- Always use full module paths like `Effects.CodebaseDiscovery` when opening modules in tests
- Example: `open Effects.CodebaseDiscovery;` instead of `open CodebaseDiscovery;`