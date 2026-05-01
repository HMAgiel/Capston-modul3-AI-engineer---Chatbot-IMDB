from state import AgentState, SupervisorOutput
from chatbot.config import model_llm, db
from chatbot.prompt.supervisor import SUPERVISOR_PROMPT
from chatbot.prompt.agent_prompt import RAG_prompt
from chatbot.tools.tool import tool_rag, tool_omdb
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_classic import hub
from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv

load_dotenv()
langfuse = get_client()

def supervisor_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm(temperature=0.1)
    llm_supervisor = llm.with_structured_output(SupervisorOutput)
    
    session_id = config.get("configurable", {}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="Supervisor",
        as_type="span",
    ):
        handler = CallbackHandler()
        
        last_message = state["messages"][-1].content
        
        
        decision = llm_supervisor.invoke(
            [
                SystemMessage(SUPERVISOR_PROMPT),
                HumanMessage(last_message),
            ],
            config = {
                "callbacks": [handler]
            },
        )
        
        if not decision:
            decision = ["basic_agent"]
        print(f"Supervisor melakukan routing ke {decision}")
        return {
            **state,
            "next_worker": decision,
        }
        
def RAG_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    RAG_llm = llm.bind_tools([tool_rag])
    session_id = config.get("configurable", {}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="RAG_worker",
        as_type="span"
    ):
        handler = CallbackHandler()
        """
        This node used to retrive data from vectore databse based on user query
        """
        
        question = state["messages"][-1].content
        history = state["history"]
        
        prompt = RAG_prompt.format(
            history=history,
            question=question
        )
        
        result = RAG_llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question}"),
            ],
            config={
                "callbacks": [handler],
            },
        )
            
        return {
            **state,
            "RAG_results": result
        }
        
def SQL_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    toolkit = SQLDatabaseToolkit(llm, db)
    tool_sql = toolkit.get_tools()
    llm_bind_tool = llm.bind_tools([tool_sql])
    session_id = config.get("configirable",{}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="SQL_agent",
        as_type="span"
    ):
        handler=CallbackHandler()
        """
        This node is to connect adn get data from sql database
        """
        
        question = state["messages"][-1].content
        history = state["messages"]
        prompt_sql = hub.pull("langchain-ai/sql-agent-system-prompt")
        prompt = prompt_sql.format(dialect=db.dialect, top_k=5)
        
        result = llm_bind_tool.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question}"),
            ],
            config={
                "callback": [handler]
            },
        )
        return {
            **state,
            "SQL_results": result
        }
        
        
        
        
        