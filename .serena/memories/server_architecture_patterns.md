# Server Architecture Patterns

## Overview
Created a modular, composable server architecture using OCaml/ReasonML module system with functors and module types for clean separation of concerns.

## Architecture Components

### 1. Module Types (Signatures)
- **AGENT_CLIENT** - Manages LangGraph SDK client instances
- **THREAD_STORE** - Handles thread persistence and retrieval
- **MESSAGE_PROCESSOR** - Processes messages and manages runs
- **REQUEST_HANDLER** - Abstracts HTTP request/response handling

### 2. Core Types
```reason
type userId = string;
type threadId = string;
type messageContent = string;
type assistantId = string;

type userMessage = { content, userId, threadId: option(threadId) };
type agentResponse = { content, threadId, runId };
```

### 3. Main Server Functor
```reason
module Server (AgentClient : AGENT_CLIENT) (ThreadStore : THREAD_STORE) 
              (MessageProcessor : MESSAGE_PROCESSOR) (RequestHandler : REQUEST_HANDLER) = {
  // Composed implementation
}
```

### 4. Concrete Implementations
- **InMemoryAgentClient** - Simple client wrapper
- **InMemoryThreadStore** - In-memory thread management
- **DefaultMessageProcessor** - Standard message processing
- **ExpressRequestHandler** - Express.js-like HTTP handling

## Key Features

### Separation of Concerns
- **Agent Logic**: Isolated in MESSAGE_PROCESSOR
- **AI Model**: Abstracted through AGENT_CLIENT  
- **HTTP Server**: Separated in REQUEST_HANDLER
- **Persistence**: Isolated in THREAD_STORE

### Composability
Different implementations can be mixed and matched:
```reason
module MyServer = Server(RedisAgentClient)(PostgresThreadStore)(CustomMessageProcessor)(FastifyRequestHandler);
```

### Request Flow
1. HTTP request comes in
2. Extract user message from request
3. Ensure thread exists for user
4. Process message through agent
5. Wait for completion
6. Send response back

### Error Handling
All operations use IO monad for consistent error handling across the entire pipeline.

## Usage Example
```reason
let serverState = createDefaultServer(~deploymentUrl="http://localhost:3002", ());
let handleRequest = (req, res) => handleExpressRequest(serverState, req, res);
```

This architecture allows for easy testing, different backend implementations, and clean separation between web framework, AI agent, and persistence layers.