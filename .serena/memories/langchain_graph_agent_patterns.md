# LangChain Graph and Agent Patterns

## Overview
Implemented comprehensive support for LangGraph StateGraph workflows and React agents with proper ReasonML abstractions.

## New Bindings Added (`src/bindings/LangChain.re`)

### StateGraph Types
- `stateGraph` - LangGraph StateGraph instance
- `messagesAnnotation` - Messages annotation for state
- `memorySaver` - Memory persistence for agents
- `reactAgent` - React agent instance
- `workflow` - Compiled graph workflow
- `tool`/`toolArray` - Tool definitions
- `graphState` - State containing messages
- `invokeResult` - Result from graph/agent execution

### StateGraph Raw Bindings
- `createStateGraph` - Create new StateGraph
- `createMemorySaver` - Create memory persistence
- `createReactAgent` - Create React agent
- `addNode'` / `addEdge'` / `addConditionalEdges'` - Graph building
- `compile'` - Compile graph to executable workflow
- `invokeWorkflow'` / `invokeReactAgent'` - Execute workflows/agents

## Graph Helper Functions (`src/model/Graph.re`)

### Graph Builder Pattern
```reason
type graphBuilder = {
  graph: stateGraph,
  nodes: list(string),
  edges: list((string, string)),
  conditionalEdges: list((string, edgeCondition)),
};
```

### High-Level Workflow Builders
- `createSimpleAgentWorkflow` - Agent + tools workflow
- `createLinearWorkflow` - Sequential node execution
- `Templates.createBasicAgentWorkflow` - Model + tools template

### Built-in Patterns
- `NodeNames` module with standard node names (start, end, agent, tools)
- `EdgeConditions` module with common routing logic
- `createModelCallNode` / `createToolCallNode` - Standard node functions

### Execution Helpers
- `runWorkflow` - Execute with message array
- `runWorkflowWithSingleMessage` - Single message execution
- `executeSimpleQuery` - Quick model + tools execution

## Agent Helper Functions (`src/model/Agent.re`)

### Agent Configuration
```reason
type agentConfig = {
  model: model,
  tools: toolArray,
  memorySaver: option(memorySaver),
  systemPrompt: option(string),
};

type agentInstance = {
  reactAgent: reactAgent,
  memorySaver: option(memorySaver),
  config: agentConfig,
};
```

### Agent Creation Patterns
- `createBasicReactAgent` - Simple model + tools
- `createReactAgentWithMemory` - With persistence
- `createReactAgentWithPrompt` - With system prompt
- `createFullReactAgent` - All options

### Conversation Management
```reason
type conversationState = {
  agent: agentInstance,
  messageHistory: list(humanMessage),
  lastResult: option(invokeResult),
};
```

### Agent Templates
- `Templates.createChatAgent` - Basic chat bot
- `Templates.createResearchAgent` - Research with tools
- `Templates.createCodeAgent` - Code assistance
- `Templates.createPersistentAgent` - With memory

### Quick Execution Functions
- `quickChat` - Instant model chat
- `quickAgentCall` - Instant agent with tools
- `chainAgents` - Run multiple agents in parallel
- `runAgentPipeline` - Sequential agent execution

## Usage Patterns

### Simple Graph Workflow
```reason
let workflow = Graph.Templates.createBasicAgentWorkflow(~model, ~tools);
let result = Graph.runWorkflowWithSingleMessage(workflow, ~content="Hello");
```

### React Agent
```reason
let agent = Agent.createBasicReactAgent(~model, ~tools);
let result = Agent.runAgentWithSingleMessage(agent, ~content="Hello");
```

### Persistent Conversation
```reason
let agent = Agent.Templates.createPersistentAgent(~model, ~tools);
let conversation = Agent.createConversation(agent)
  |> Agent.addMessageToConversation(~content="Hello")
  |> Agent.runConversationStep;
```

The architecture provides both low-level graph building capabilities and high-level agent abstractions while maintaining clean separation between bindings and helper functions.