from chatbot.graph.state import SupervisorOutput, DataAgentOutput, AgentState
from chatbot.config import model_llm, db
from chatbot.prompt.supervisor import SUPERVISOR_PROMPT
from chatbot.prompt.agent_prompt import RAG_prompt, omdb_prompt, Data_prompt, SQL_tambahan_prompt,agregasi_prompt, Basic_prompt
from chatbot.tools.tool import RAG_tool, OMDB_tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
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
                HumanMessage(f"last_message: {last_message}"),
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
            "next_worker": main_route,
            "SQL_result": "",
            "RAG_result": "",
            "OMDB_result": ""
        }       

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
        history  = state["history"]
        
        prompt = Data_prompt.format(
            history=history,
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
        butuh_rag = result.get("needs_overview", False)
   
        if sql_results != "" and data_route == "SQL_agent":
            if "EMPTY_RESULT" in sql_results: 
                print("🚨 [Guardrail] Data kosong di SQL. Memaksa pindah ke Agregasi_agent.")
                data_route = "Agregasi_agent"
            else:
                if butuh_rag == True and rag_results == "":
                    print("🚨 [Guardrail] SQL selesai. Memaksa lanjut ke RAG_agent untuk overview.")
                    data_route = "RAG_agent"
                elif omdb_results == "":
                    print("🚨 [Guardrail] SQL selesai. Lanjut cari detail tambahan ke OMDB_agent.")
                    data_route = "OMDB_agent"
                else:
                    data_route = "Agregasi_agent"

        elif butuh_rag == True and rag_results == "" and data_route in ["Agregasi_agent", "OMDB_agent"]:
            print("🚨 [Guardrail] Tunggu! User butuh overview, RAG belum jalan. Memaksa pindah ke RAG_agent.")
            data_route = "RAG_agent"

        elif omdb_results != "" and data_route in ["OMDB_agent", "SQL_agent"]:
            print("🚨 [Guardrail] OMDB sudah dicoba. Memaksa pindah ke Agregasi_agent.")
            data_route = "Agregasi_agent"
            
        elif rag_results != "" and data_route in ["RAG_agent", "SQL_agent", "OMDB_agent"]:
            print("🚨 [Guardrail] RAG sudah dicoba. Memaksa pindah ke Agregasi_agent.")
            data_route = "Agregasi_agent"
                
        return {
            "data_worker": data_route
        }
        
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
        hasil_sql = state.get("SQL_result", "")
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
        
        if "N/A" in response.content:
            result = "Tidak pake RAG"
        else:
            result = RAG_tool.invoke({"query": response.content})
            
        return {
            "RAG_result": result
        }
        
def SQL_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm(temperature=0.1)
    session_id = config.get("configurable", {}).get("session_id", "default")

    with langfuse.start_as_current_observation(name="SQL_agent", as_type="span"):
        handler = CallbackHandler()

        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        SQL_tools = toolkit.get_tools()
        tools_map = {tool.name: tool for tool in SQL_tools}
        SQL_llm = llm.bind_tools(SQL_tools)

        prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        prompt_sql = prompt_template.format(
            dialect=db.dialect,
            top_k="this number is based on what user want in default use '10' but if user want 5 yse 5 if want more or less do it as user specifiy")

        question = state["messages"][-1].content
        history = state["history"]

        messages = [
            SystemMessage(content=prompt_sql),
            HumanMessage(content=f"Query: {question}\n\nHistory: {history}"),
        ]

        MAX_ITERATIONS = 10 
        iteration = 0

        while iteration < MAX_ITERATIONS:
            iteration += 1

            response: AIMessage = SQL_llm.invoke(
                messages,
                config={"callbacks": [handler]},
            )
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id   = tool_call["id"]

                try:
                    tool = tools_map[tool_name]
                    tool_output = tool.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error executing tool: {str(e)}"
                    
                messages.append(
                    ToolMessage(
                        content=str(tool_output),
                        tool_call_id=tool_id,
                        name=tool_name,
                    )
                )

        else:
            response = AIMessage(content="EMPTY_RESULT")

        return {
            "SQL_result": response.content,
        }
        
        
def OMDB_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    session_id = config.get("configurable",{}).get("session_id", "default")
    with langfuse.start_as_current_observation(
        name="OMDB_agent",
        as_type="span"
    ):
        handler = CallbackHandler()
        """
        This node used to get data from OMDB server
        """
        hasil_sql = state.get("SQL_result", "")
        question = state["messages"][-1].content
        history = state["history"]
        
        prompt = omdb_prompt
        
        response = llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question} \n\n SQL history: {hasil_sql} \n\n Chat History: {history}"),
            ],
            config={
                "callbacks": [handler],
            },
        )
        
        if "N/A" in response.content:
            result = "Tidak pake OMDB"
        else:
            clean_title = [judul.strip() for judul in response.content.split(',')]
            result = OMDB_tool.invoke({"film_title": clean_title})
            
        return {
            "OMDB_result": result
        }
        
def Agregasi_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    llm = model_llm()
    session_id = config.get("configurable",{}).get("session_id", "default")
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
        history_chat = f"User: {original_query} | AI: {final}"
        return {
            **state,
            "messages": [AIMessage(content=final)],
            "history": [history_chat],
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
        question = state["messages"][-1].content

        prompt = Basic_prompt
        result = llm.invoke(
            [
                SystemMessage(prompt),
                HumanMessage(f"Query: {question}"),
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