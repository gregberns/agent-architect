# Codebase Structure

The codebase is organized into several key directories:

- **src/**: Main source code directory
  - **domain/**: Contains domain models and types
    - `Actor.re`: Actor record definition and related functions
    - `ActorId.re`: Actor identifier type
    - `ActorType.re`: Types of actors (likely Broker, Carrier)
    - `Auth.re`: Authentication related types and functions
    - `AuthActor.re`: Actor authentication functionality
    - `Mail.re`: Mailbox and messaging functionality
    - `State.re`: State representation
    - `StateAction.re`: Actions that can change state
    - `Task.re`: Task representation
    - `TaskId.re`: Task identifier type

  - **state-machine/**: State machine implementation
    - `Command.re`: Command definitions
    - `Event.re`: Event definitions
    - `Mutate.re`: State mutation functions
    - `State.re`: State representation for the state machine
    - `StateMachine2.re`: Main state machine implementation
    - `StateMutation.re`: State mutation type definitions
    - **interfaces/**: Interface definitions for state machine components

  - **sm-impl/**: State machine implementation details
    - `CommandHandler_RegisterActor.re`: Handler for registering actors
    - `CommandProcessor.re`: Processes commands
    - `Services.re`: Services used by the state machine
    - `StateProcessor.re`: Processes state changes
    - **types/**: Type definitions for the implementation

  - **world/**: World model implementation

- **docs/**: Documentation
  - `TECH_SPEC.md`: Technical specification of the system

- **public/**: Public assets
  - `index.html`: Main HTML file for the web application