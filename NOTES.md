`I keep my thoughts here`

# models.py

**StepStatus** - Will be used to store API requests responses and results.

**Candidate** - A dataclass for tracking a candidate in the process.

**Command** - Based on LangGraph's command. A basic dataclass for node communication.

# nodes.py
Each task in the instructions is represented by a function.
Each function represents a graph node.
Each func receives a candidate and spme input, performs the node's logics, and returns a command.
TODO: relationship between tasks of the same step.

# graph.py
**Step** - class that represents a step in the process. it can have sub tasks and be hidden (for steps that somw candidates will not need)

**FLOW** - Responsible of ordering steps.

**_ALL_TASKS_** - A module derived from `FLOW` and is used for getting next task in the flow.

# tests

Written by Claude Sonnet 4.6
