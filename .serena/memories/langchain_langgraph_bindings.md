# LangChain and LangGraph SDK Bindings

## Overview
Added comprehensive bindings for LangChain and LangGraph SDK to enable ReasonML/Melange interop with the JavaScript library.

## Files Created/Updated
- `src/bindings/LangChain.re` - Complete bindings for LangChain and LangGraph SDK
- `src/model/Server.re` - ReasonML implementation example using the bindings

## LangGraph SDK Bindings Added
The bindings now include support for:

### Types
- `client` - LangGraph SDK client
- `clientConfig` - Configuration for client with apiUrl
- `threadResponse` - Response from thread creation with thread_id
- `runResponse` - Response from run creation with run_id  
- `runInput` - Input for runs containing messages array
- `runConfig` - Configuration for runs with input and optional multitaskStrategy

### Functions
- `createClient(~apiUrl)` - Creates a new LangGraph client
- `createThread(client)` - Creates a new thread, returns IO.t(threadResponse, Js.Exn.t)
- `createRun(client, ~threadId, ~assistantId, ~input, ~multitaskStrategy?, ())` - Creates a run
- `joinRun(client, ~threadId, ~runId)` - Waits for a run to complete
- `createRunInput(messages)` - Helper to create run input from message array

## Pattern Implementation
The ReasonML implementation in Server.re follows the exact same flow as the JavaScript example:
1. Create client with deployment URL
2. Create thread
3. Create first run (will be interrupted)
4. Create second run with multitask strategy
5. Join/wait for second run completion

## Usage Example
```reason
let client = createClient(~apiUrl="https://your-deployment.com");
let exampleRunner = createServerExample(~deploymentUrl, ());
exampleRunner() |> IO.unsafeRunAsync(...);
```

All operations are properly wrapped in the IO monad following the project's error handling patterns.