# Code Style and Conventions

From examining the codebase, the following style and conventions can be observed:

- **File Extensions**:
  - `.re` files: ReasonML syntax
  - `.ml` files: OCaml syntax

- **Module Structure**:
  - Each domain concept has its own module
  - Types are often defined with `type t = ...` pattern
  - Modules are organized by domain area (`domain`, `state-machine`, etc.)

- **Functional Approach**:
  - The codebase follows the "Functional Core, Imperative Shell" pattern
  - Uses Relude library for functional programming constructs
  - All modules are opened with `-open Relude.Globals` compiler flag

- **Record Types**:
  - Domain objects are represented as records (e.g., `Actor.t`)
  - Properties follow camelCase naming convention

- **Project Organization**:
  - JS Bindings in `bindings/` directory
  - Tooling utilities in `effects/` directory

- **Dune Configuration**:
  - Libraries are built with `(modes melange)` for JavaScript output
  - Multiple output targets for different environments (React, Node.js)
