from langchain_core.tools import tool
from chatbot.config import retrive, rerank_model, url_omdb, api_omdb
import requests
import os

@tool
def RAG_tool(query: str) -> str:
    """This tools is used to call data from Qdrant based on user query"""
    retrive_rag = retrive
    rerank = rerank_model()
    results = retrive_rag.similarity_search(query=query, k=5)
    hasil_rag = [result.page_content for result in results]
    reranking = rerank.rank(
    query, 
    hasil_rag,
    return_documents=True, 
    top_k=3
    )
    context_list = [item['text'] for item in reranking]
    return context_list
    
tool_rag = [RAG_tool]

@tool
def OMDB_tool(film_title: str) -> str:
    """"This tool for calling OMDB data when data from other source is null, none or NaN.
    Input FILM_title in specific """
    
    url = url_omdb

    params = {
        "apikey": api_omdb,
        "t": film_title
    }

    response = requests.get(url, params=params)

    data = response.json()
    
    return data
tool_omdb = [OMDB_tool]

if __name__ == "__main__":
    from langchain_openai import ChatOpenAI
    from dotenv import load_dotenv
    from langchain.agents import create_agent
    
    load_dotenv()

    llm = ChatOpenAI(model="gpt-4o-mini")
    
    SYSTEM_PROMPT = """You are an agent for get the data from OMDb APi database, retrive the data from what title of film user ask.
    if user input typo title fix it
    """

    agent_app = create_agent(
        llm,
        tool_omdb,
        system_prompt=SYSTEM_PROMPT
    )
    # Test 1: Pertanyaan Produk
    print("=" * 60)
    print("TEST 1: Rekomendasi Produk")
    print("=" * 60)

    response = agent_app.invoke(
        {"messages": [{"role": "user", "content": "i watch a series last night with my brother its called breaking bad, so i want to know what the artis name adn info of the movie?"}]}
    )
    answer = response["messages"][-1].content
    print(answer)
    
    