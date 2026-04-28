from typing import TypedDict, List, Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    
    RAG_result: str
    sql_result: str
    history: list
    next_worker: List[Literal["RAG_agent", "SQL_agent", "basic_agent"]]
    
    final_result: str
    
class SupervisorOutput(TypedDict):
    next_worker: List[Literal["RAG_agent", "SQL_agent", "basic_agent"]]