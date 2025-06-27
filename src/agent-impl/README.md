# Agent Inner Working Demonstration

## Setup

### Initialize the Env

```
cd src/agent-impl/bootstrap-agent
uv venv --python 3.11
source ./.venv/bin/activate
uv pip install -r requirements.txt
```

### LLM Setup

In this demo, we'll use Gemini through OpenRouter.

```py
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    base_url="https://openrouter.ai/api/v1"
)

MODEL_NAME = "google/gemini-2.5-pro-preview"
```

**ACTION**

* Signup with OpenRouter
* Get an API Key
* Option: I'd suggest throwing a couple bucks at them to get some tokens, but there are models that are free (Maybe use DeepSeek? https://openrouter.ai/models?q=free)
* Create an `.env` file in the root (next to the `agent.py` file)
* Add the API key to `.env`: `OPENAI_API_KEY=<<API_KEY>>`

### Startup

```
source ./.venv/bin/activate
python agent.py
```

## Learning Workflow

Instructions:

* Terminal Session 1: Start a terminal with the original agent - run all the commands below in it.
* Terminal Session 2: Open a second terminal, after each code change, restart the agent/process to see the changes made.

### Phase 1 - Extend Conversation History / Context

This will take the conversation history - which is a simple array - and convert it into a class that writes to a log file.

Purpose: You can see everything in history. This is also your whole context thats passed to 

```
conversation_history = [ ] # This is initialized with the system message

# This function will take your whole conversation history, and pass it to the LLM to process.
# This is how the LLM has the past messages you've discussed
stream = client.chat.completions.create(
    model=MODEL_NAME,
    messages=conversation_history,
    tools=tools,
    stream=True
)
```

#### Step 1 - Change

```
Prompt> Read file `./agent.py`. We're going to make improvements to that file. Its an LLM agent. The first thing we want to do is take th
e `conversation_history` variable, which is an array, and change that to a class which we can intercept all changes - `append`, `clear`,
`extend`, and iterating over the array, so that we know any time the array is changing. Please stub in two function calls that do nothing
 for now, but will: 1) capture the new record any time a new record is appended 2) if the array is significantly modified the whole array
 is passed into the function. Lets call function #1 `append_write` and function #2 `whole_write`.
```

**Expected**

* There should be a class for `ConversationHistory`
* The variable `conversation_history` should be the `ConversationHistory` class

**Action**

* New Terminal: Open venv, start agent, test that everything seems to work

#### Step 2 - Change

```
Prompt> Now, lets add a global variable thats going to represent the path of the log file we want to write to. For now, the value will be
 hard coded to `../logs/conversation_history.log`. Then update the `append_write` function to append the record to the file. The record s
hould be written in JSON format, so the Dict needs to be converted to JSON, and a new line should be appended after the JSON object. The
`whole_write` function needs to be updated to write to the log file - the function should overwrite the conversation_history file - every
 message in history should be written as a json object separated by a new line. So append should add a json record (like in jsonl format)
, and  whole_write should overwrite the file in jsonl format.
```

**Action**

* Other Terminal: Restart Agent. Ask "Whats 2+2". View `../logs/conversation_history.log`

**Expected**

* You should see a system message, user message, and agent response.

#### Step 3 - Demonstration 

```
Prompt> Read the `requirements.txt` file
```

**Output**

```json
{"role": "user", "content": "Read the `requirements.txt` file"}
{"role": "assistant", "content": null, "tool_calls": [{"id": "tool_0_read_file", "type": "function", "function": {"name": "read_file", "arguments": "{\"file_path\":\"requirements.txt\"}"}}]}
{"role": "tool", "tool_call_id": "tool_0_read_file", "content": "Content of file '<YOUR PATH>/bootstrap-agent/requirements.txt':\n\nopenai\npydantic\npython-dotenv\nrich\nprompt_toolkit\npytest\n"}
{"role": "assistant", "content": "!I see the contents of `requirements.txt`. It's a standard Python dependency file.\n\nDo you have any questions about it, or is there something you'd like me to do with this information? For instance, I can tell you about these packages, suggest adding version constraints for reproducibility, or look for other parts of the project that use them."}
```

What's happening:

* User requests a file to be read
* LLM sends back an empty content but a fill 'tool_calls' property, which says "Call the 'read_file' tool with argument `file_path=requirements.txt`
  * This agent code has already defined which tool calls are available in the System Message.
  * See the `execute_function_call` function in the agent to see whats going on
  * The `read_file` tool is called, the file is read, and puts the contents into a string
* The agent appends a new message with `'role': 'tool'` and the contents of the file - then sends this whole payload back to the LLM
* The LLM then responds, acknowledging it has seen the file



### Phase #2 - Stream Contents

The agents which humans are going to see generally will be set up to to stream results back - meaning as the tokens come out of the LLM they'll be passed back to the user so its visible the progress being made.

Next lets look at the 

#### Step 1 - Change

```
Prompt> In `process_streaming_response`, the `for` loop has a `chunk` variable. We want to write that variable to a different log file `.
./logs/stream_chunks.log`. Create a function that will accept a chunk, and write the chunk to the log file in JSON formatting. The file s
hould be in JSONL formatting - so each JSON chunk needs to end with a new line.
```

**Expected Change**

* There should now be a function that writes to a new log file
* The `for` loop should be calling the new function with the `chunk` variable

#### Step 2 - Demo

Switch to your second terminal, restart it.

```
Prompt> In `requirements.txt`, whats the first dependency and what is it for?
```

**Output**

* View the `../logs/stream_chunks.log` 
* A couple properties to check out:
  * `"tool_calls"`
  * `"finish_reason"`
  * `"native_finish_reason"`
  * `"usage"`


```json
{"choices": [{"delta": {"content": "", "role": "assistant", "reasoning": "**Examining Dependencies'**\n\nI've started by inspecting the `requirements.txt` file. My initial task involves pinpointing the primary dependency. Subsequently, I'll investigate its purpose to offer a detailed explanation, ensuring my analysis is comprehensive.\n\n\n"}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}]   }
{"choices": [{"delta": {"content": null, "role": "assistant", "tool_calls": [{"index": 0, "id": "tool_0_read_file", "function": {"arguments": "{\"file_path\":\"requirements.txt\"}", "name": "read_file"}, "type": "function"}]}, "finish_reason": "tool_calls", "index": 0, "logprobs": null, "native_finish_reason": "STOP"}]   }
{"choices": [{"delta": {"content": "", "role": "assistant"}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}], "usage": {"completion_tokens": 47, "prompt_tokens": 567, "total_tokens": 614}, }
{"choices": [{"delta": {"content": "", "role": "assistant", "reasoning": "**Understanding Dependencies' Purpose**\n\nI've reviewed the `requirements.txt` file; the initial dependency is `openai`. My next step involves articulating the purpose of this library within the project's context. I believe I know its role, so now I'll formulate the explanation.\n\n\n"}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}] }
{"choices": [{"delta": {"content": "", "role": "assistant", "reasoning": "**Articulating OpenAI's Role**\n\nI've decided to explicitly state that `openai` is the initial dependency. After that, I'll explain that it grants access to the OpenAI API and its varied models. My next step is to streamline the explanation to be as clear as possible for the user.\n\n\n"}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}]}
{"choices": [{"delta": {"content": "Based on the file content, the first dependency listed in `requirements.txt` is `openai`.\n\nThis is the official Python client", "role": "assistant", "reasoning": null}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}] }
{"choices": [{"delta": {"content": " library for the OpenAI API. It allows developers to easily interact with OpenAI's language models, such as GPT-3 and GPT-4, directly from their Python applications. It's essential for any application that needs to leverage OpenAI's AI", "role": "assistant", "reasoning": null}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}] }
{"choices": [{"delta": {"content": " capabilities.", "role": "assistant", "reasoning": null}, "finish_reason": "stop", "index": 0, "logprobs": null, "native_finish_reason": "STOP"}] }
{"choices": [{"delta": {"content": "", "role": "assistant"}, "finish_reason": null, "index": 0, "logprobs": null, "native_finish_reason": null}], "usage": {"completion_tokens": 208, "prompt_tokens": 635, "total_tokens": 843} }
```


```json
[{
  "choices": [
    {
      "delta": {
        "content": "",
        "role": "assistant",
        "reasoning": "**Examining Dependencies'**\n\nI've started by inspecting the `requirements.txt` file. My initial task involves pinpointing the primary dependency. Subsequently, I'll investigate its purpose to offer a detailed explanation, ensuring my analysis is comprehensive.\n\n\n"
      },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ]
},
{
  "choices": [
    {
      "delta": {
        "content": null,
        "role": "assistant",
        "tool_calls": [
          {
            "index": 0,
            "id": "tool_0_read_file",
            "function": {
              "arguments": "{\"file_path\":\"requirements.txt\"}",
              "name": "read_file"
            },
            "type": "function"
          }
        ]
      },
      "finish_reason": "tool_calls",
      "index": 0,
      "logprobs": null,
      "native_finish_reason": "STOP"
    }
  ]
},
{
  "choices": [
    {
      "delta": { "content": "", "role": "assistant" },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ],
  "usage": {
    "completion_tokens": 47,
    "prompt_tokens": 567,
    "total_tokens": 614
  }
},
{
  "choices": [
    {
      "delta": {
        "content": "",
        "role": "assistant",
        "reasoning": "**Understanding Dependencies' Purpose**\n\nI've reviewed the `requirements.txt` file; the initial dependency is `openai`. My next step involves articulating the purpose of this library within the project's context. I believe I know its role, so now I'll formulate the explanation.\n\n\n"
      },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ]
},
{
  "choices": [
    {
      "delta": {
        "content": "",
        "role": "assistant",
        "reasoning": "**Articulating OpenAI's Role**\n\nI've decided to explicitly state that `openai` is the initial dependency. After that, I'll explain that it grants access to the OpenAI API and its varied models. My next step is to streamline the explanation to be as clear as possible for the user.\n\n\n"
      },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ]
},
{
  "choices": [
    {
      "delta": {
        "content": "Based on the file content, the first dependency listed in `requirements.txt` is `openai`.\n\nThis is the official Python client",
        "role": "assistant",
        "reasoning": null
      },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ]
},
{
  "choices": [
    {
      "delta": {
        "content": " library for the OpenAI API. It allows developers to easily interact with OpenAI's language models, such as GPT-3 and GPT-4, directly from their Python applications. It's essential for any application that needs to leverage OpenAI's AI",
        "role": "assistant",
        "reasoning": null
      },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ]
},
{
  "choices": [
    {
      "delta": {
        "content": " capabilities.",
        "role": "assistant",
        "reasoning": null
      },
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "native_finish_reason": "STOP"
    }
  ]
},
{
  "choices": [
    {
      "delta": { "content": "", "role": "assistant" },
      "finish_reason": null,
      "index": 0,
      "logprobs": null,
      "native_finish_reason": null
    }
  ],
  "usage": {
    "completion_tokens": 208,
    "prompt_tokens": 635,
    "total_tokens": 843
  }
}]
```




