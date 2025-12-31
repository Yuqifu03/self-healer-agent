from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

AgentPhase = Literal[
    "analyze_error",
    "locate_code",
    "propose_fix",
    "apply_fix",
    "validate",
    "done",
    "failed"
]

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_file: str
    last_error: str
    iteration_count: int
    is_fixed: bool
    phase: AgentPhase