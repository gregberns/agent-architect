

## Agent Logging Framework

* Write to log file - JSONL
* Server watches file, streams changes, pushes/publishes messages to UI
* Maybe messages are raw to start with
* Displayed in a chat style
* Messages then refined - parsed and turned into a particular structure (StreamChunk, etc) (hmmm this already exists, how to know type??)


## Conversation History

Convert array  - intercept appends/changes, then update a 'conversation history file' - maybe just write whole contents??

1) Add logging of all incoming messages as json
2) When memory is updated, that also needs to be logged


Two log files:
* Current Stream - to see whats happening
* Conversation History




## Improvemenets

Token Usage tracking
Memory - its only keeping 15-20 messages - can increase that or track tokens
