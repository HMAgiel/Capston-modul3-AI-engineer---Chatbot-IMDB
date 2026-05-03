import uuid
from chatbot.graph.graph import app
from langfuse import get_client, propagate_attributes
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv

load_dotenv()
langfuse = get_client()


CURRENT_SESSION_ID = str(uuid.uuid4())

def run_chatbot(query: str):
    
    print(f"\n{'='*55}")
    print(f"Query: {query}")
    print(f"Session: {CURRENT_SESSION_ID}")
    print(f"{'='*55}")

    with langfuse.start_as_current_observation(
        name="langgraph-supervisor",
        as_type="trace",
        input={"query": query}
    ) as obs:
        with propagate_attributes(session_id=CURRENT_SESSION_ID):

            handler = CallbackHandler()
            
            result = app.invoke(
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
                        "session_id": CURRENT_SESSION_ID,
                        "thread_id": CURRENT_SESSION_ID
                        },
                },
            )
            
            obs.update(output={"response": result.get("final_result", "")})

    print("\nFinal answer:")
    print(result.get("final_result", "Maaf, tidak ada jawaban."))
    print(f"Cek langfuse di : https://cloud.langfuse.com -> session {CURRENT_SESSION_ID}")
    
if __name__ == "__main__":
    print("🤖 Chatbot Capston3 Siap! (Ketik 'q' untuk keluar)")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ['q', 'quit', 'stop', 's']:
            print("Sampai jumpa!")
            break
        else:
            run_chatbot(user_input)