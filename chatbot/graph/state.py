from typing import TypedDict, List, Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class SupervisorOutput(TypedDict):
    next_worker: Literal["Data_agent", "basic_agent"]
    
class DataAgentOutput(TypedDict):
    data_worker: Literal["RAG_agent", "SQL_agent", "OMDB_agent", "Agregasi_agent"]

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    
    RAG_result: str
    SQL_result: str
    OMDB_result: str
    history: list
    data_worker: Literal["RAG_agent", "SQL_agent", "OMDB_agent"]
    next_worker: Literal["Data_agent", "basic_agent"]
    final_result: str
    
