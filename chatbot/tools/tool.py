from langchain_core.tools import tool
from chatbot.config import retrive, rerank, url_omdb, api_omdb
import requests
import os

@tool
def RAG_tool(query: str) -> str:
    """This tools is used to call data from Qdrant based on user query"""
    retrive_rag = retrive
    rerank_model = rerank
    results = retrive_rag.similarity_search(query=query, k=5)
    hasil_rag = [result.page_content for result in results]
    reranking = rerank_model.rank(
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
    
    