
## Objective

We want to start to put together the components of an AI Agent system.

The end goal will to be build a multi agent system that can perform various coding tasks, such as testing, writing code, planning system layout, and existing system analysis.

But to start, we need to put together all the components to build a simple agent.

Some system requirements:
* The agent system will need to operate both autonomously and at times include human interaction. For example, once a coding task is completed by Agent1, Agent2 will be tasked with testing the resulting changes. Agent1's coding tasks may be supervised by a human, but then Agent2's testing would be done in the background to verify the code.
* We'll want to untilize both Agents and Workflows. Workflows are a series of semi-deterministic tasks that will be executed that may or may not involve a model. For example, when testing, we'll need to attempt to 1) compile and lint the code 2) run its tests 3) analyze the code for poor structure or patterns and 4) report any resulting issues. Since that series of tasks will be executed everytime, a workflow is more appropriate to use.

System Structure and Best Practices:
* We'll be writing the system with ReasonML and the Melange compiler. ReasonML is a derivative of OCaml. The ReasonML will transpile to Javascript.
* LangChain and LangGraph libraries will be used for now to interact with the LLM's. We'll be using the JavaScript libraries and will write Melange bindings to interact with the Javascript libraries.
* The system needs to be built in a modular way. OCaml supports `module types`, `module functors`, and various other methods of separating logic and execution. The "Function Core, Imperative Shell" or "Hexagonal Architecture" patterns will be very valuable here. 
  * We'll want to structure the code so as much logic can be embedded into the Functional Core


## Project Structure


* Bindings
  * The bindings are in the "Imperative Shell" part of the architecture. 
  * Folder Location: `./src/bindings`
  * LangChain Bindings: `./src/bindings/LangChain.re`
    * We'll want to keep LangChain totally out of the 'core' part of the architecture

* 



https://langchain-ai.github.io/langgraphjs/agents/agents/



* Need a Tools interface that tools can implement
* Prompt interfaces
  * Static or Dynamic
  * https://langchain-ai.github.io/langgraphjs/agents/agents/#custom-prompts
* Memory - to checkpoint conversations
  * To allow multi-turn conversations with an agent, you need to enable persistence by providing a checkpointer when creating an agent. At runtime you need to provide a config containing thread_id — a unique identifier for the conversation (session)   https://langchain-ai.github.io/langgraphjs/agents/agents/#memory
* Context: https://langchain-ai.github.io/langgraphjs/agents/context/
  * Context includes any data outside the message list that can shape agent behavior or tool execution. This can be:
    * Information passed at runtime, like a user_id or API credentials.
    * Internal state updated during a multi-step reasoning process.
    * Persistent memory or facts from previous interactions.

## Basic Interfaces

* Agent.invoke( <<Payload>> )
  * Agent.invoke can emit different error types
    * https://langchain-ai.github.io/langgraphjs/agents/run_agents/#max-iterations
* Payload: { messages: Array( <<Message>> )}
  * messages: A list of all messages exchanged during execution (user input, assistant replies, tool invocations).
* Message: { role: string, content: string }

```
const agent = createReactAgent(...);

const response = await agent.invoke(
  { messages: [ { role: "user", content: "what is the weather in sf" } ] }
);
```


#### Config (static context)

Config is for immutable data like user metadata or API keys. Use when you have values that don't change mid-run.

Specify configuration using a key called "configurable" which is reserved for this purpose:

```
await agent.invoke(
  { messages: "hi!" },
  { configurable: { userId: "user_123" } }
)
```

#### Streaming - Emitting Events

https://langchain-ai.github.io/langgraphjs/agents/streaming/#tool-updates


