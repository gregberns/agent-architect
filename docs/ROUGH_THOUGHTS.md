


* Integrate existing static analisys tools 
* Identify relationships between modules/projects, and think about coupling/cohesion
* interfaces are clean, clear, modules are only exposing what they need,
  * Modules are well structured

* Once issues are identifed, the framework to address them is critical
  * Prioitization - go through all the issues, classify them (should be going in in a consistent way)

  * Should agents know about each other? 
    * Could there be a manager that knows what agent should be allocated specific problem types?

* Can we use smaller (cheaper) models to compare sections of code for similarity, redundancy, reuse?
  * How could scale/scope/impact of change - or what part of the code will be touched - and how will that impact other things that need to be done?
  * As changed go through parts of the system, what kind of changes are needed? Are they sprawling? or can discrete changes be made to a series of modules, that turn into a feature?
    * When sprawling changes are needed - then architecture needs to be re-evaluated

* As code/files change, prior created data will decay over time. Before proitization - an agent may need to review

* Capture runtime logs, qa logs (Maybe not part of this project)


How can I make this architect robust, easy work with and extend
