Best practices for JavaScript bindings in ReasonML/Melange:

1. **Separate bindings from business logic**:
   - All JavaScript bindings should be in the src/bindings/ directory
   - Node.js specific bindings go in src/bindings/NodeJs.re
   - Import bindings using: `open Bindings.NodeJs;`

2. **Wrap external functions with IO**:
   - All external JS functions that can throw should be wrapped in IO.triesJS
   - Create a private external binding with a trailing apostrophe (e.g., readFileSync')
   - Provide an IO-wrapped public version without apostrophe

   Example:
   ```reason
   module Fs = {
     [@bs.module "fs"] external readFileSync': (string, [@bs.string] [`utf8]) => string = "readFileSync";
     let readFileSync = (path, encoding) => IO.triesJS(() => readFileSync'(path, encoding));
   }
   ```

3. **Organization**:
   - Group related bindings in modules (Fs, Path, Http, etc.)
   - Export types used by bindings (e.g., nodeStats)
   - Keep raw externals private, expose only IO-wrapped versions

4. **Error handling**:
   - Use IO.catchError(_ => IO.pure(defaultValue)) for graceful fallbacks
   - Use IO.triesJS for JS function calls that might throw
   - Avoid try/catch blocks in favor of IO monads

5. **List operations with IO**:
   - Use List.traverse(IO.applicative, fn) instead of List.flatMap for IO operations
   - Use List.contains(~f=String.eq(value), list) for string containment checks

6. **File system operations**:
   - Always wrap Node.js file system calls in IO
   - Provide sensible defaults for error cases (empty lists, None values)
   - Use synchronous operations for simplicity where appropriate