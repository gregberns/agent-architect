open Relude.Globals;
open Bindings.LangChain;

/**
 * Agent.re - Helper functions for creating and managing LangChain agents
 *
 * This module provides high-level abstractions for creating different types
 * of agents, particularly focusing on React agents and agent workflows.
 *
 * Based on the JavaScript pattern:
 *
 * const agentCheckpointer = new MemorySaver();
 * const agent = createReactAgent({
 *   llm: agentModel,
 *   tools: agentTools,
 *   checkpointSaver: agentCheckpointer,
 * });
 */

/* Agent configuration types */
type agentConfig = {
  model,
  tools: toolArray,
  memorySaver: option(memorySaver),
  systemPrompt: option(string),
};

type agentInstance = {
  reactAgent,
  memorySaver: option(memorySaver),
  config: agentConfig,
};

/* Agent creation helpers */
let createBasicAgentConfig = (~model: model, ~tools: toolArray): agentConfig => {
  {
    model,
    tools,
    memorySaver: None,
    systemPrompt: None,
  };
};

let createAgentConfigWithMemory =
    (~model: model, ~tools: toolArray, ~memorySaver: memorySaver): agentConfig => {
  {
    model,
    tools,
    memorySaver: Some(memorySaver),
    systemPrompt: None,
  };
};

let createAgentConfigWithPrompt =
    (~model: model, ~tools: toolArray, ~systemPrompt: string): agentConfig => {
  {
    model,
    tools,
    memorySaver: None,
    systemPrompt: Some(systemPrompt),
  };
};

let createFullAgentConfig =
    (
      ~model: model,
      ~tools: toolArray,
      ~memorySaver: memorySaver,
      ~systemPrompt: string,
    )
    : agentConfig => {
  {
    model,
    tools,
    memorySaver: Some(memorySaver),
    systemPrompt: Some(systemPrompt),
  };
};

/* React agent creation */
let createReactAgentFromConfig = (config: agentConfig): agentInstance => {
  let memorySaver =
    switch (config.memorySaver) {
    | Some(saver) => saver
    | None => createMemorySaver()
    };

  let reactAgent =
    createReactAgent(
      ~llm=config.model,
      ~tools=config.tools,
      ~checkpointSaver=memorySaver,
    );

  {
    reactAgent,
    memorySaver: Some(memorySaver),
    config,
  };
};

let createBasicReactAgent = (~model: model, ~tools: toolArray): agentInstance => {
  let config = createBasicAgentConfig(~model, ~tools);
  createReactAgentFromConfig(config);
};

let createReactAgentWithMemory =
    (~model: model, ~tools: toolArray, ~memorySaver: memorySaver)
    : agentInstance => {
  let config = createAgentConfigWithMemory(~model, ~tools, ~memorySaver);
  createReactAgentFromConfig(config);
};

let createReactAgentWithPrompt =
    (~model: model, ~tools: toolArray, ~systemPrompt: string): agentInstance => {
  let config = createAgentConfigWithPrompt(~model, ~tools, ~systemPrompt);
  createReactAgentFromConfig(config);
};

let createFullReactAgent =
    (
      ~model: model,
      ~tools: toolArray,
      ~memorySaver: memorySaver,
      ~systemPrompt: string,
    )
    : agentInstance => {
  let config =
    createFullAgentConfig(~model, ~tools, ~memorySaver, ~systemPrompt);
  createReactAgentFromConfig(config);
};

/* Agent execution helpers */
let runAgent =
    (agent: agentInstance, ~messages: array(humanMessage))
    : IO.t(invokeResult, Js.Exn.t) => {
  let state = createGraphState(messages);
  invokeReactAgent(agent.reactAgent, state);
};

let runAgentWithSingleMessage =
    (agent: agentInstance, ~content: string): IO.t(invokeResult, Js.Exn.t) => {
  let message = createHumanMessage(content);
  let messages = [|message|];
  runAgent(agent, ~messages);
};

let runAgentWithConversation =
    (agent: agentInstance, ~conversation: list(string))
    : IO.t(invokeResult, Js.Exn.t) => {
  let messages = List.map(createHumanMessage, conversation) |> List.toArray;
  runAgent(agent, ~messages);
};

/* Agent management helpers */
let getAgentMemorySaver = (agent: agentInstance): option(memorySaver) => {
  agent.memorySaver;
};

let getAgentConfig = (agent: agentInstance): agentConfig => {
  agent.config;
};

let updateAgentTools =
    (agent: agentInstance, ~newTools: toolArray): agentInstance => {
  let updatedConfig = {
    ...agent.config,
    tools: newTools,
  };
  createReactAgentFromConfig(updatedConfig);
};

let updateAgentModel = (agent: agentInstance, ~newModel: model): agentInstance => {
  let updatedConfig = {
    ...agent.config,
    model: newModel,
  };
  createReactAgentFromConfig(updatedConfig);
};

/* Conversation management */
type conversationState = {
  agent: agentInstance,
  messageHistory: list(humanMessage),
  lastResult: option(invokeResult),
};

let createConversation = (agent: agentInstance): conversationState => {
  {
    agent,
    messageHistory: [],
    lastResult: None,
  };
};

let addMessageToConversation =
    (conversation: conversationState, ~content: string): conversationState => {
  let message = createHumanMessage(content);
  {
    ...conversation,
    messageHistory: List.cons(message, conversation.messageHistory),
  };
};

let runConversationStep =
    (conversation: conversationState): IO.t(conversationState, Js.Exn.t) => {
  let messages = List.reverse(conversation.messageHistory) |> List.toArray;
  runAgent(conversation.agent, ~messages)
  |> IO.map(result => {
       {
         ...conversation,
         lastResult: Some(result),
       }
     });
};

let getLastResponse = (conversation: conversationState): option(string) => {
  switch (conversation.lastResult) {
  | Some(result) =>
    // Extract content from the last message in the result
    let messageCount = Array.length(result.messages);
    if (messageCount > 0) {
      // In a real implementation, would extract actual content from the message
      Some
        ("Agent response"); // Placeholder
    } else {
      None;
    };
  | None => None
  };
};

/* Predefined agent templates */
module Templates = {
  let createChatAgent = (~model: model): agentInstance => {
    let emptyTools = [||]; // No tools for basic chat
    createBasicReactAgent(~model, ~tools=emptyTools);
  };

  let createResearchAgent =
      (~model: model, ~searchTool: tool, ~webTool: tool): agentInstance => {
    let tools = [|searchTool, webTool|];
    let systemPrompt = "You are a research assistant. Use the available tools to gather information and provide comprehensive answers.";
    createReactAgentWithPrompt(~model, ~tools, ~systemPrompt);
  };

  let createCodeAgent = (~model: model, ~codeTool: tool): agentInstance => {
    let tools = [|codeTool|];
    let systemPrompt = "You are a coding assistant. Help users write, debug, and understand code.";
    createReactAgentWithPrompt(~model, ~tools, ~systemPrompt);
  };

  let createPersistentAgent =
      (~model: model, ~tools: toolArray): agentInstance => {
    let memorySaver = createMemorySaver();
    createReactAgentWithMemory(~model, ~tools, ~memorySaver);
  };
};

/* Convenience functions for quick agent creation and usage */
let quickChat =
    (~model: model, ~message: string): IO.t(invokeResult, Js.Exn.t) => {
  let agent = Templates.createChatAgent(~model);
  runAgentWithSingleMessage(agent, ~content=message);
};

let quickAgentCall =
    (~model: model, ~tools: toolArray, ~message: string)
    : IO.t(invokeResult, Js.Exn.t) => {
  let agent = createBasicReactAgent(~model, ~tools);
  runAgentWithSingleMessage(agent, ~content=message);
};

/* Agent composition helpers */
let chainAgents =
    (agents: list(agentInstance), ~message: string)
    : IO.t(list(invokeResult), Js.Exn.t) => {
  List.IO.traverse(
    agent => runAgentWithSingleMessage(agent, ~content=message),
    agents,
  );
};

let runAgentPipeline =
    (agents: list(agentInstance), ~initialMessage: string)
    : IO.t(invokeResult, Js.Exn.t) => {
  // Run agents in sequence, passing output of one to the next
  // For now, simplified to just run the first agent
  switch (agents) {
  | [agent, ..._rest] =>
    runAgentWithSingleMessage(agent, ~content=initialMessage)
  | [] => IO.throw(Js.Exn.raiseError("No agents provided to pipeline"))
  };
};
