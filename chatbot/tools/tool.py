from langchain_core.tools import tool
from chatbot.config import retrive, rerank, url_omdb, api_omdb
import requests
from typing import List
import requests
import json
import os

@tool
def RAG_tool(query: str) -> str:
    """This tools is used to call data from Qdrant based on user query"""
    retrive_rag = retrive
    rerank_model = rerank
    results = retrive_rag.similarity_search(query=query)
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
def OMDB_tool(film_titles: List[str]) -> str:
    """
    This tool is for calling OMDb data when data from other sources is null, none, or NaN.
    Input must be a LIST of movie titles. For example: ["Shaun of the Dead", "Hot Fuzz"]
    """
    url = url_omdb
    all_results = [] # Siapkan list kosong untuk menampung semua hasil

    # Looping setiap judul film yang diberikan oleh LLM
    for title in film_titles:
        params = {
            "apikey": api_omdb,
            "t": title
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                all_results.append(f"Error untuk '{title}': API mengembalikan status {response.status_code}.")
                continue
                
            data = response.json()
            
            if data.get("Response") == "False":
                all_results.append(f"OMDb tidak dapat menemukan film '{title}'.")
            else:
                all_results.append(data)
                
        except Exception as e:
            all_results.append(f"Error memproses '{title}': {str(e)}")

    # Gabungkan semua hasil menjadi satu string JSON agar mudah dibaca LLM
    return json.dumps(all_results, indent=2)
tool_omdb = [OMDB_tool]
    
    