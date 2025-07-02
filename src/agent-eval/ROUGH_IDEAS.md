## Shower Thoughts



* Cleanup the Terminal printing to just be ASCII (Wont look as pretty)
* Output Docker logs straight to file
* Could logs be written to 'output' directory? Or log

## Evolution


### Evolution File Structure

epoch-000/
  validation/
    agent-src/

epoch-001/
  evolution/
    # Should include metadata about where this agent came from
    agent-src/  # Copied from parent epoch
      agent.py
      Dockerfile
      requirments.txt
    input
      agent.py
      Dockerfile
      requirments.txt
      TASK.md
    output
      # Before completing, the agent should have the following files
      agent.py
      Dockerfile
      requirments.txt
      TASK.md
  validation/
    # Pretty much the same format





### Eliciting Constant Improvement

Without explicity saying what to change, how do you elicit evolutionary behavior?

* Can you use environmental stimuli to invoke specifc changes?
  * The problems/challenges that are given,

* Build a script that will analyze the chain of agents that have been created during evolution.
  * Turn that into a mermaid diagram for visualization. And print out an image. 
  * Each child agent should have a reference to its parent.

Processing log files - use smaller model for summarization

## Agent Capabilities

## Tools

* File diff'ing/comparison
  * Merging two agents
  * Integrating two sets of code

* Record/track the tokens used

* Code Execution

* RandoMan:
  * Integrate a better conversational memory
  * Sophisticated model to compress the memory
  * Persist memory across conversations
    * Store best practices and make sure that they continue to be used across sessions.
  * Automated storing/integrating storage of memories into the process
  * Record the memory
  * Different models for different tasks. 
  * Code writing and execution
  * Use the Devstral model

## Knowledge

Provide a config that points to a folder with docs, or a set of docs, that is either
* Always pulled in for each start of the agent
* Or searchable/indexed into an in-line knowledge base

* Memory in agents - different patterns - https://github.com/RichmondAlake/memorizz

## Problem Decomposition

* Decompose problem into sub parts - then test that the interfaces work together.
  * Each sub part is managed by its own agent - somehow the agents are created dynamically - and can be switched between. maybe an agent manages only a single file or folder??
  * What if we own that 'Whatevers Law" where a sowftware system looks like its org structure

## Models

* Models: Try this. Might be good and fast for some coding tasks.
  * May not be good at writing code - but maybe could read code, or make fixed to ReasonML code
  * https://openrouter.ai/qwen/qwen3-30b-a3b

* Using smaller models for specialized tasks to reduce costs
  * Task: Find/replace code blocks
  * Could we swap out Models for different parts of the agent?
  * How can we evaluate a model for partiuclar attributes? Reasoning, planning, coding, testing}}
  * model focused on diffing - and make the agent hand that off. 
  * Could also read the code to understand whats going on - processing a code fle with a large model becomes expensive. Putting summaries into memory would be interesting.
  * By function with an AST ???
  * Could LSP work be driven off smaller model?

* Logic RAG systems to represent actual logic and reasoning
  * https://youtu.be/wzXBXGVbItE?si=B1vU4Grc4-hs0aCg&t=866

* LLM Graph Transformer - LangChain
  * Outputs a structured format (JSON) of the graph data
  * https://youtu.be/O-T_6KOXML4?si=SvcIZKDKnInWpckn&t=783


## Prompt Evolution to Agent Evolution

What if the testing framework was altered a bit. Instead of the task being passed to an LLM directly, some set of information (a task or code base) is passed via some mechanism to the agent. A docker container could be loaded with
* the agent code repository
* a file with the task in it
* a volume mount that once the agent completed the task would execute a command (bash script to copy the file) - "Completed task" - which could be a git command - but in this case would copy the new agent code.
* (Future) Document repository of ideas that the LLM could use to do research and explore ideas of how to improve itself.
Instead of 'prompts' its a list of children that end up getting executed, the results returned, and tested.
What should the prompt be when the agent is trying to improve on itself? How do you trigger the agent to execute - "Do stuff please"? The parent agent which is going to generate a child (or children), needs instructions built in so it knows what to do. The parent should be able to update the instructions in the child.
Maybe there is an initialization prompt that the parent is passed... "You are an agent that is capable of creating new versions of yourself. You can determine the future instructions the 'future you' can follow by changing the 'initialization prompt'". That prompt is the one used to kick off (edited) 


## Agent Action Framework

Create a Redux style framework to handle the foundations of the inputs and outputs from the LLMs - to support the creation of Agents
* Decode Data structures of the models - meaning the models are sending structures back
  * Structures from the LLM's are decoded, and maybe named - if we know what the thing is
* Allow mapping from Data Structure to an Action needed
* The Actions taken need to be tracked, (We could replay them really easily... see below)
Tasks handled??
1. Logs them as JSONL (used to understand responses that werent handled or handled correctly)
2. Data pulled from response(decode into type), then a decision is made what to do with it - there is an Action generated
   * This could be just writing the contents, or a function call
   * Should log the data + Action, so this can be inspected later to make sure it was the correct decision
   * When the 'write stream' is occurring, we'd want to track tokens, how many writes, have an 'append' to a current message (or something)
3. The Action is then executed (and logged, that it's going to occur). This could be some type of Action Handler thing.
   * The Inputs are logged. The Handler can log all the steps. The resulting thing can be logged
   * A Tool Call could be required. All the parameters
Replaying actions:
* For Testing purposes, the actions could be re-run (start on action 5, run to action 32).
  * What if state is updated/tracked, then we can test whether the state is what we want it to be
