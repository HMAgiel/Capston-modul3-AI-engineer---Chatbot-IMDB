from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from chatbot.graph.state import AgentState
from chatbot.graph.agent import supervisor_agent, Data_agent, SQL_agent, RAG_agent, OMDB_agent, Agregasi_agent, basic_agent

workflow = StateGraph(AgentState)

workflow.add_node("supervisor_agent", supervisor_agent)
workflow.add_node("basic_agent", basic_agent)
workflow.add_node("Data_agent", Data_agent)
workflow.add_node("SQL_agent", SQL_agent)
workflow.add_node("RAG_agent", RAG_agent)
workflow.add_node("OMDB_agent", OMDB_agent)
workflow.add_node("Agregasi_agent", Agregasi_agent)

workflow.add_edge(START, "supervisor_agent")

workflow.add_conditional_edges(
    "supervisor_agent",
    lambda state: state["next_worker"],
    {
        "basic_agent": "basic_agent",
        "Data_agent": "Data_agent"
    }
)

workflow.add_edge("basic_agent", END)

workflow.add_conditional_edges(
    "Data_agent",
    lambda state: state["data_worker"],
    {
        "SQL_agent": "SQL_agent",
        "RAG_agent": "RAG_agent",
        "OMDB_agent": "OMDB_agent",
        "Agregasi_agent": "Agregasi_agent"
    }
)

workflow.add_edge("SQL_agent", "Data_agent")
workflow.add_edge("RAG_agent", "Data_agent")
workflow.add_edge("OMDB_agent", "Data_agent")

workflow.add_edge("Agregasi_agent", END)

memory = MemorySaver()

app = workflow.compile(checkpointer=memory)