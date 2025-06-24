

## Task Execution

* The TaskGenerator will build the whole data structure thats going to be executed
  * It needs to generate everything as a unique task - so if there are multiple repetitions created, there is no nesting

* TaskQueue
  * A generic mechanism that will process work
  * Both "AgentEvolution" and "AgentEvaluation" will be handled through this

## Agent Execution

* "AgentEvolution"
  * A specific version of the Agent will be chosen and 'n' instances will attempt to improve itself
  * The agent needs to be sent a task - to improve a version of itself
  * The "agent under test" and "code to change" directories
    * "agent under test" - Agent that will be executing the commands
    * "code to change" - A version of the agent that will be evolved
      * The paper seems to suggest that the agent can choose ANY version - seems like it should take its parent
      * Has a "Task.md" file that the instance kicks off with?
  * ____
    * It probably needs a 'workspace' to execute against
      * Inputs: 
        * Source code
        * Data sets
      * Working Directory:
        * Edit Source code
        * Memory
      * Output:
        * New source code of agent
        * Data sets the agent can use to 
  * Agent Startup procedure
    * When an agent is starting, there may need to be a series of scripts executed?? (`npm install`)
  * Embedded prompt
    * The agent should have an embedded prompt that it can evolve itself. When the 'evolve' command is executed, it executes that prompt.

* "AgentEvaluation"
  * A specific version of the Agent will be passed tasks/problems to handle. 
    * There needs to be a 'human-less' version - meaning there's some type of API exposed, and the agent can execute on the task and return results


```sh
cd src/agent-eval/agent-src
TASK_ID=task-001 docker-compose up --build



```


How could the execution environment be tuned for the language?
* Python, Js, ReasonML - 



# Task Training

* The Agent can be passed "training" tasks to try and process, but durring evaluation, they need to be passed a set of "test" tasks that it hasn't seen before
