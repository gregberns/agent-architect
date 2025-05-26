# OCaml/ReasonML Debugging Tips

## Common Compiler Errors and Solutions

### 1. "Unbound record field" Error

When you see an error like `Unbound record field identity_token`, this usually means one of:

- **Missing type annotation**: When destructuring a record, add a type annotation so the compiler knows which record type you're referring to:
  ```reasonml
  // Error:
  ({field1, field2} as record) => ...
  
  // Fix - add type annotation:
  ({field1, field2} as record: MyModule.MyRecord.t) => ...
  ```

- **Missing module qualifier**: If the field is defined in a module, ensure you're using the full path:
  ```reasonml
  // Error:
  field: value
  
  // Fix - add module qualifier:
  Module.submodule.field: value
  ```

- **Unknown record type for inline record**: When creating an inline record without a type context:
  ```reasonml
  // Error:
  let message = {
    to_: mailbox_address,
    from: AdminMailer,
    expected_response: Informational,
  };
  
  // Fix - add type annotation:
  let message: Domain.Mail.MailboxMessage.t = { ... };
  
  // Better fix - inline the record where it's used:
  NewTask(SendMessage({
    to_: mailbox_address,
    from: AdminMailer,
    expected_response: Informational,
  }));
  ```

### 2. "Missing record field pattern" Warning

When destructuring a record but not using all fields, you'll get this warning:
```
Error (warning 9 [missing-record-field-pattern]): the following labels are not bound in this record pattern:
field1, field2, field3
Either bind these labels explicitly or add '; _' to the pattern.
```

Fix by adding an underscore to indicate you're aware of the remaining fields:
```reasonml
// Error:
({field1, field2} as record: MyRecord.t) => ...

// Fix - add underscore for remaining fields:
({field1, field2, _} as record: MyRecord.t) => ...
```

### 3. Module Path Issues

When using nested modules, ensure you're using the correct path:
```reasonml
// For a field inside a nested module:
Domain.Mail.MailboxAddress.AdminMailer
```

### 4. Record Field Lookup

For record fields with special characters (like underscore), use the correct syntax:
```reasonml
// For a field named "to_":
{
  to_: value,
  from: otherValue
}
```

### 5. Debugging with Serena

- Use `mcp__serena__get_symbols_overview` to understand the structure of files
- Use `mcp__serena__find_symbol` to locate specific symbols and their types
- Always examine existing code patterns before writing new code