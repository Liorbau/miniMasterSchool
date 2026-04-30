`System design ideas and decisions made along the way`

# types.py

**StepStatus** - Will be used to store API requests responses and results.

**Candidate** - A dataclass for tracking a candidate in the process.

**Command** - Based on LangGraph's command. A basic dataclass for node communication.

# nodes.py
Each task in the instructions is represented by a function.
Each function represents a graph node.
Each func receives a candidate and spme input, performs the node's logics, and returns a command.
TODO: relationship between tasks of the same step.