from langchain.tools import tool
from chatbot.config import embedding_model, retrive_rag, rerank_model

@tool
def RAG_tool(query: str) -> str:
    """This tools is used to call data from Qdrant based on user query"""
    embedding = embedding_model()
    retrive = retrive_rag(embedding)
    rerank = rerank_model(device='cuda')
    results = retrive.similarity_search(query=query, k=5)
    hasil_rag = [result.page_content for result in results]
    reranking = rerank.rank(
    query, 
    hasil_rag,
    return_documents=True, 
    top_k=3
    )
    context_list = [item['text'] for item in reranking]
    return context_list
    
tools = [RAG_tool]