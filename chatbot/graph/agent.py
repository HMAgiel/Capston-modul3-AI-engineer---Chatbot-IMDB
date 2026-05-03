from chatbot.graph.state import SupervisorOutput, DataAgentOutput, AgentState
from chatbot.config import model_llm, db
from chatbot.prompt.supervisor import SUPERVISOR_PROMPT
from chatbot.prompt.agent_prompt import RAG_prompt, omdb_prompt, Data_prompt, agregasi_prompt, Basic_prompt
from chatbot.tools.tool import RAG_tool, tool_omdb
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import create_agent
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
        
        if decision and "next_worker" in decision:
            main_route = decision["next_worker"]
        else:
            main_route = "basic_agent"
            
        if isinstance(main_route, list):
            main_route = main_route[0]
            
        return {
            "next_worker": main_route
        }        
        # if not decision:
        #     decision = ["basic_agent"]
        # print(f"Supervisor melakukan routing ke {decision}")
        # return {
        #     **state,
        #     "next_worker": decision,
        # }


def Data_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm(temperature=0.1)
    llm_data = llm.with_structured_output(DataAgentOutput)
    session_id = config.get("configurable", {}).get("session_id", "default")
    
    with langfuse.start_as_current_observation(
        name="Data_agent",
        as_type="span",
    ):
        handler = CallbackHandler()
        """
        This agnet is used to sort what agent used for the data search
        """
        sql_results = state.get("SQL_result", "")
        omdb_results = state.get("OMDB_result", "")
        rag_results = state.get("RAG_result", "")
        question = state["messages"][-1].content
        
        # Optional: log untuk debug routing decision
        print(f"[Data_agent] SQL='{sql_results[:50]}' RAG='{rag_results[:50]}' OMDB='{omdb_results[:50]}'")
        
        prompt = Data_prompt.format(
            question=question,
            RAG_result=rag_results,
            SQL_result=sql_results,
            OMDB_result=omdb_results
        )
        
        result = llm_data.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question}")
            ],
            config={
                "callbacks": [handler],
            },
        )
            
        data_route = result.get("data_worker", "Agregasi_agent")
        
        return {
            "data_worker": data_route
        }
        
        # return {
        #     **state,
        #     "data_worker": result
        # }
        
        
def RAG_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    session_id = config.get("configurable", {}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="RAG_agnet",
        as_type="span"
    ):
        handler = CallbackHandler()
        """
        This node used to retrive data from vectore databse based on user query
        """
        hasil_sql = state.get("SQL_results", "")
        question = state["messages"][-1].content
        history = state["history"]
        
        prompt = RAG_prompt.format(
            question=question,
            SQL_result=hasil_sql

        )
        
        response = llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question} \n\n History: {history}"),
            ],
            config={
                "callbacks": [handler],
            },
        )
        
        # Gunakan response.content untuk mengambil teks dari AIMessage
        if "N/A" in response.content:
            result = "Tidak pake RAG"
        else:
            # Panggil tool dengan key 'query' dan value berupa text
            result = RAG_tool.invoke({"query": response.content})
            
        return {
            "RAG_result": result
        }
        
def SQL_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm(temperature=0.1)
    session_id = config.get("configirable",{}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="SQL_agent",
        as_type="span"
    ):
        handler=CallbackHandler()
        """
        This node is to connect adn get data from sql database
        """
        
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        question = state["messages"][-1].content
        history = state["history"]
        prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        agent_sql = create_agent(
            model=llm,
            tools=toolkit.get_tools(),
            system_prompt=prompt_template.format(dialect=db.dialect, top_k=5)
        )
        
        # ... (kode di atasnya tetap sama) ...
        events = agent_sql.stream(
            {"messages": [("user", question), ("History", history)]},
            stream_mode="values"
        )
        
        final_answer = ""
        for event in events:
            # Print ke terminal (seperti yang sudah kamu buat)
            event["messages"][-1].pretty_print()
            
            # Tangkap teks jawabannya setiap kali berputar
            final_answer = event["messages"][-1].content
            
        print(f"[SQL Agent] Selesai. Jawaban dikirim ke state: {final_answer}")
        
        # INI KUNCI YANG HILANG: Kembalikan datanya ke State!
        # Pastikan nama key-nya ("SQL_result" atau "SQL_results") sama persis dengan yang ada di AgentState-mu
        return {
            "SQL_result": final_answer 
        }
            
            
            
        #     {"messages": [("user", question)]},
        #     config={"callbacks": [handler]}
        # )
        
        # result = response.get("output", "")
        
        # return {
        #     "SQL_result": result
        # }
        
        
def OMDB_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    omdb_llm = llm.bind_tools(tool_omdb)
    session_id = config.get("configirable",{}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="OMDB_agent",
        as_type="span"
    ):
        handler = CallbackHandler()
        """
        This node used to get data from OMDB server
        """
        hasil_sql = state.get("SQL_result", "")
        history = state["history"]
        prompt = omdb_prompt.format(
            hasil_sql=hasil_sql
        )
        
        result = omdb_llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {hasil_sql} \n\n History: {history}"),
            ],
            config={
                "callbacks": [handler],
            },
        )
            
        return {
            "OMDB_result": result
        }
        
def Agregasi_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    session_id = config.get("configirable",{}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="Agregasi_agent",
        as_type="span"
    ):
        handler=CallbackHandler()
        """
        This node is for agregation of all the data agent output
        """
        results = []
        if state.get("RAG_result"):
            results.append(f"RAG Result: {state["RAG_result"]}")
        if state.get("SQL_result"):
            results.append(f"SQL Result: {state["SQL_result"]}")
        if state.get("OMDB_result"):
            results.append(f"OMDB result: {state["OMDB_result"]}")
        combined = "\n\n".join(results) if results else "Tidak ada hasil dari worker"
        
        history = state["history"]
        original_query = state["messages"][-1].content
        
        result = llm.invoke(
            [
                SystemMessage(agregasi_prompt),
                HumanMessage(f"Query: {original_query}\n\n History: {history}\n\n data: {combined}")
            ],
            config={
                "callbacks": [handler],
            },
        )
        
        final = result.content
        return {
            **state,
            "messages": [AIMessage(content=final)],
            "final_result": final,
        }
        
def basic_agent(state: AgentState, config: RunnableConfig)-> AgentState:
    llm=model_llm()
    session_id = config.get("configurable", {}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="Basic_agent",
        as_type="span"
    ):

        handler = CallbackHandler()
        """
        Node ini menjawab pertanyaan umum yang tidak masuk kategori
        produk atau promo.
        """
        question = state["messages"][0]
        history  = state["history"]

        prompt = Basic_prompt.format(
            history=history,
            question=question,
        )
        result = llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question} \n\n History: {history}"),
            ],
            config={
                "callbacks": [handler],
            },
        )
        basic_results = result.content
        return {
            **state,
            "messages": [AIMessage(content=basic_results)],
            "final_result": basic_results,
        }