# Task Completion Checklist

When completing a task in this project, you should:

1. **Build the project** to ensure changes compile correctly:
   ```
   npm run build
   ```

2. **Format the code** to ensure it follows OCaml/ReasonML style guidelines:
   ```
   npm run format
   ```

3. **Check formatting** (without modifying) to verify style compliance:
   ```
   npm run format-check
   ```

4. **Run tests** (if available):
   There doesn't appear to be an explicit test command in package.json, but the project includes Jest in its dependencies, so likely tests would be run with:
   ```
   npm test
   ```
   
5. **Bundle and serve** the application to verify functionality:
   ```
   npm run bundle
   npm run serve
   ```

When developing, you can use:
- `npm run watch` to automatically rebuild on file changes
- `npm run serve` to run the development server