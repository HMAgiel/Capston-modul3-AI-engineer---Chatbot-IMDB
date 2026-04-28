from state import AgentState, SupervisorOutput
from chatbot.config import model_llm
from chatbot.prompt.supervisor import SUPERVISOR_PROMPT
from chatbot.prompt.agent_prompt import RAG_prompt
from chatbot.tools.tool import RAG_tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
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
    
    session_id = config.get("cinfigurable", {}).get("session_id", "default")
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
            history=history
            question=question
        )
        
        response = llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question}"),
            ],
            config={
                "callbacks": [handler],
            },
        )
        hasil_query = response.content.strip()
        
        if "N/A" in hasil_query:
            result = "[Tidak ada input ke database]"
        else:
            result = RAG_tool.invoke(hasil_query)
            
        return {
            **state,
            "RAG_results": result
        }