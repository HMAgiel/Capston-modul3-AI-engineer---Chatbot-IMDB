import uuid
import streamlit as st
from langfuse import get_client, propagate_attributes
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv
 
# ── Ganti ini dengan import graph kamu ──────────────────────────
from chatbot.graph.graph import app as langgraph_app
# ────────────────────────────────────────────────────────────────
 
load_dotenv()
langfuse = get_client()
 
# ── Session state init ───────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
 
if "messages" not in st.session_state:
    st.session_state.messages = []          # list of {"role": "user"|"assistant", "content": str}
 
 
# ── Core function (sekarang return final_result) ─────────────────
def run_chatbot(query: str) -> str:
    session_id = st.session_state.session_id
 
    with langfuse.start_as_current_observation(
        name="langgraph-supervisor",
        as_type="trace",
        input={"query": query}
    ) as obs:
        with propagate_attributes(session_id=session_id):
            handler = CallbackHandler()
 
            result = langgraph_app.invoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "SQL_result": "",
                    "RAG_result": "",
                    "OMDB_result": "",
                    "history": [],
                    "final_result": "",
                    "data_worker": "",
                    "next_worker": ""
                },
                config={
                    "callbacks": [handler],
                    "configurable": {
                        "session_id": session_id,
                        "thread_id": session_id,
                    },
                },
            )
 
            final = result.get("final_result", "_(tidak ada respons)_")
            obs.update(output={"response": final})
            return final