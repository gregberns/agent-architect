open Relude.Globals;
open Bindings.LangChain;

/**
 * Graph.re - Helper functions for building LangGraph StateGraph workflows
 *
 * This module provides higher-level abstractions for creating and managing
 * StateGraph workflows, making it easier to build complex agent workflows.
 *
 * Based on the JavaScript pattern:
 *
 * const workflow = new StateGraph(MessagesAnnotation)
 *   .addNode("agent", callModel)
 *   .addEdge("__start__", "agent")
 *   .addNode("tools", toolNode)
 *   .addEdge("tools", "agent")
 *   .addConditionalEdges("agent", shouldContinue);
 * const app = workflow.compile();
 */

/* Graph builder types and functions */
type graphBuilder = {
  graph: stateGraph,
  nodes: list(string),
  edges: list((string, string)),
  conditionalEdges: list((string, edgeCondition)),
};

/* Node function types for common patterns */
type modelNode = graphState => IO.t(graphState, Js.Exn.t);
type toolNode = graphState => IO.t(graphState, Js.Exn.t);
type agentNode = graphState => IO.t(graphState, Js.Exn.t);

/* Built-in node names */
module NodeNames = {
  let start = "__start__";
  let end_ = "__end__";
  let agent = "agent";
  let tools = "tools";
  let human = "human";
};

/* Built-in edge conditions */
module EdgeConditions = {
  let shouldContinue = (state: graphState): string => {
    // This would typically check if the last message indicates the agent should continue
    // For now, simple logic - if there are messages, continue to tools, otherwise end
    let messageCount = Array.length(state.messages);
    if (messageCount > 0) {
      NodeNames.tools;
    } else {
      NodeNames.end_;
    };
  };

  let shouldEndWorkflow = (_state: graphState): string => {
    NodeNames.end_;
  };

  let shouldGoToAgent = (_state: graphState): string => {
    NodeNames.agent;
  };
};

/* Graph builder functions */
let createGraphBuilder = (): graphBuilder => {
  let graph = createStateGraph();
  {
    graph,
    nodes: [],
    edges: [],
    conditionalEdges: [],
  };
};

let addNodeToBuilder =
    (builder: graphBuilder, ~name: string, ~nodeFunction: nodeFunction)
    : graphBuilder => {
  let updatedGraph = addNode(builder.graph, ~name, ~nodeFunction);
  {
    ...builder,
    graph: updatedGraph,
    nodes: [name, ...builder.nodes],
  };
};

let addEdgeToBuilder =
    (builder: graphBuilder, ~from: string, ~to_: string): graphBuilder => {
  let updatedGraph = addEdge(builder.graph, ~from, ~to_);
  {
    ...builder,
    graph: updatedGraph,
    edges: [(from, to_), ...builder.edges],
  };
};

let addConditionalEdgeToBuilder =
    (builder: graphBuilder, ~from: string, ~condition: edgeCondition)
    : graphBuilder => {
  let updatedGraph = addConditionalEdges(builder.graph, ~from, ~condition);
  {
    ...builder,
    graph: updatedGraph,
    conditionalEdges: [(from, condition), ...builder.conditionalEdges],
  };
};

let compileGraph = (builder: graphBuilder): workflow => {
  compile(builder.graph);
};

/* High-level workflow builders */
let createSimpleAgentWorkflow =
    (~agentFunction: nodeFunction, ~toolFunction: nodeFunction): workflow => {
  createGraphBuilder()
  |> addNodeToBuilder(~name=NodeNames.agent, ~nodeFunction=agentFunction)
  |> addNodeToBuilder(~name=NodeNames.tools, ~nodeFunction=toolFunction)
  |> addEdgeToBuilder(~from=NodeNames.start, ~to_=NodeNames.agent)
  |> addEdgeToBuilder(~from=NodeNames.tools, ~to_=NodeNames.agent)
  |> addConditionalEdgeToBuilder(
       ~from=NodeNames.agent,
       ~condition=EdgeConditions.shouldContinue,
     )
  |> compileGraph;
};

let createLinearWorkflow =
    (nodeSequence: list((string, nodeFunction))): workflow => {
  let builder = createGraphBuilder();

  let builderWithNodes =
    List.foldLeft(
      (acc, (name, nodeFunction)) =>
        addNodeToBuilder(acc, ~name, ~nodeFunction),
      builder,
      nodeSequence,
    );

  let nodeNames = List.map(((name, _)) => name, nodeSequence);
  let pairs = List.zip(List.cons(NodeNames.start, nodeNames), nodeNames);

  let builderWithEdges =
    List.foldLeft(
      (acc, (from, to_)) => addEdgeToBuilder(acc, ~from, ~to_),
      builderWithNodes,
      pairs,
    );

  compileGraph(builderWithEdges);
};

/* Workflow execution helpers */
let runWorkflow =
    (workflow: workflow, ~messages: array(humanMessage))
    : IO.t(invokeResult, Js.Exn.t) => {
  let state = createGraphState(messages);
  invokeWorkflow(workflow, state);
};

let runWorkflowWithSingleMessage =
    (workflow: workflow, ~content: string): IO.t(invokeResult, Js.Exn.t) => {
  let message = createHumanMessage(content);
  let messages = [|message|];
  runWorkflow(workflow, ~messages);
};

/* Node function helpers */
let createModelCallNode = (_model: model): nodeFunction => {
  ({messages} as state: graphState) => {
    // Convert human messages to invoke the model
    // This is a simplified version - in practice would need proper message handling
    let lastMessage = messages |> Array.last;

    switch (lastMessage) {
    | Some(_message) =>
      // In a real implementation, we'd extract content from the message and call the model
      // For now, return the state unchanged wrapped in a promise
      Js.Promise.resolve(state)
    | None => Js.Promise.resolve(state)
    };
  };
};

let createToolCallNode = (_tools: toolArray): nodeFunction => {
  (state: graphState) => {
    // Tool execution logic would go here
    // For now, return state unchanged
    Js.Promise.resolve(
      state,
    );
  };
};

let createPassthroughNode = (): nodeFunction => {
  (state: graphState) => {
    Js.Promise.resolve(state);
  };
};

/* Workflow templates */
module Templates = {
  let createBasicAgentWorkflow = (~model: model, ~tools: toolArray): workflow => {
    let agentNode = createModelCallNode(model);
    let toolNode = createToolCallNode(tools);
    createSimpleAgentWorkflow(
      ~agentFunction=agentNode,
      ~toolFunction=toolNode,
    );
  };

  let createSimpleChain = (nodeNames: list(string)): workflow => {
    let nodeSequence =
      List.map(name => (name, createPassthroughNode()), nodeNames);
    createLinearWorkflow(nodeSequence);
  };
};

/* Convenience functions for common patterns */
let executeSimpleQuery =
    (~model: model, ~tools: toolArray, ~query: string)
    : IO.t(invokeResult, Js.Exn.t) => {
  let workflow = Templates.createBasicAgentWorkflow(~model, ~tools);
  runWorkflowWithSingleMessage(workflow, ~content=query);
};

let createCheckpointedWorkflow =
    (~model: model, ~tools: toolArray, ~memorySaver as _: memorySaver)
    : workflow => {
  // In a full implementation, this would integrate the memorySaver with the workflow
  // For now, create a basic workflow
  Templates.createBasicAgentWorkflow(
    ~model,
    ~tools,
  );
};
