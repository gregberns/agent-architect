# Updated Code Style and Conventions

In addition to the observed style conventions, the following rules MUST be followed:

## Naming Conventions
- Use **camelCase** for all variable and record field names (e.g., `identityToken`, not `identity_token`)
- Use PascalCase for module names and type constructors
- Consistent naming across the codebase is essential

## Functional Programming Style
- Use pipe operator `|>` as much as possible to reduce variable declarations
- Minimize use of `let` bindings
- Prefer `fun` pattern matching over `switch` statements when possible
- Chain operations using pipes rather than creating intermediate variables
- Use point-free style when possible (avoid explicitly naming arguments that are immediately passed to the next function)
- **Inline records** when they are only used once - don't create separate bindings

## Record Access
- ALWAYS use record destructuring to access properties instead of dot notation
- Instead of `record.field`, use pattern matching: `({field} as record) => field`
- In function parameters, prefer destructuring: `({field1, field2}: MyRecord.t) => ...`
- When accessing multiple fields, use the pattern: `({field1, field2, ...} as record)`
- When destructuring but not using all fields, add underscore: `({field1, field2, _} as record: MyRecord.t)`
- If a field name might conflict with a parameter name, use an alias: `({identityToken: actorIdentityToken, _} as actor)`

## Type Annotations
- Always add type annotations when destructuring records to avoid "Unbound record field" errors
- When using nested modules, include the full path for type annotations: `Domain.Actor.t`
- For functions that return records, annotate the return type: `: Transform.t =>`

## Pattern Examples

### Avoid:
```reasonml
let maybeActor = Map.get(actorId, state.actors);

switch (maybeActor) {
| None => Transform.NoOpState
| Some(actor) => {
    // Using dot notation
    let mailbox_address = actor.mailbox_address; // snake_case
  }
};
```

### Prefer:
```reasonml
Map.get(actorId, state.actors)
|> Option.fold(
     Transform.NoOpState,
     ({mailboxAddress, _} as actor: Domain.Actor.t) => { // camelCase
       // Using destructured mailboxAddress directly
     },
   );
```

### Avoid:
```reasonml
let message = {
  to_: mailboxAddress,
  from: AdminMailer,
  expected_response: Informational,
};

NewTask(SendMessage(message));
```

### Prefer:
```reasonml
// Inline the record directly where it's used
NewTask(SendMessage({
  to_: mailboxAddress,
  from: AdminMailer,
  expected_response: Informational,
}));
```

These style conventions should be applied consistently across all new code.