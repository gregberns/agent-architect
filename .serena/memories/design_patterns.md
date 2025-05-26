# Design Patterns and Guidelines

Based on examining the codebase and documentation, the following design patterns and guidelines are apparent:

## Architectural Patterns
1. **Functional Core, Imperative Shell**
   - Core logic is functional and pure
   - IO and effects are pushed to the outer layers
   - Services are used to interact with the outside world

2. **Command Pattern**
   - Commands represent actions that can be executed against the system
   - Each command is associated with an actor
   - Commands are processed sequentially

3. **Event Sourcing**
   - State changes generate events
   - Events can trigger additional tasks or state changes

4. **State Machine**
   - System state transitions based on commands
   - Computed state changes are applied deterministically

## Domain Guidelines
1. **Actor-based Model**
   - Actors represent external entities taking actions
   - Actors go through lifecycle stages (Register, Claim, Verify)
   - Actors can be associated with Brokers or Carriers

2. **Clearly Defined Interface**
   - Interface is clearly defined for LLM models to understand
   - Functions are grouped by actor type
   - All functions describe their purpose, inputs, and outputs

3. **Task Processing**
   - System can generate asynchronous tasks
   - Tasks have labels and payloads
   - Tasks can be processed independently

## Code Guidelines
1. **Modular Design**
   - Functionality is split into small, focused modules
   - Types are defined in their own modules
   - Related functionality is grouped together

2. **Functional Programming**
   - Immutable data structures
   - Pure functions where possible
   - Use of functional programming concepts (Option types, etc.)