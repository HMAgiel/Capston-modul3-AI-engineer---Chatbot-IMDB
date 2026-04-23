from langchain_core.tools import tool
from chatbot.config import embedding_model, retrive_rag, rerank_model

@tool
def RAG_tool(query: str) -> str:
    """This tools is used to call data from Qdrant based on user query"""
    embedding = embedding_model()
    retrive = retrive_rag(embedding)
    rerank = rerank_model()
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

if __name__ == "__main__":
    from langchain_openai import ChatOpenAI
    from dotenv import load_dotenv
    from langchain.agents import create_agent
    load_dotenv()

    llm = ChatOpenAI(model="gpt-4o-mini")
    
    SYSTEM_PROMPT = """You are an agent for retrive the document of RAG from user query, your job is to take user query and see what user intention and rewrite to be more efficeint query.
    If user query is in langunage other tahn english tranlate it first adn rewrite it before call the tool for RAG
    """

    agent_app = create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT
    )
    # Test 1: Pertanyaan Produk
    print("=" * 60)
    print("TEST 1: Rekomendasi Produk")
    print("=" * 60)

    response = agent_app.invoke(
        {"messages": [{"role": "user", "content": "Saya penasaran saya kan belajar sejarah disekolah, nah apakah ada perang mengenai perang dunia ke 2?"}]}
    )
    answer = response["messages"][-1].content
    print(answer)
    # print("✅ Agent berhasil dibuat!")
    # print(f"   Model  : {llm.model_name}")
    # print(f"   Tools  : {[t.name for t in tools]}")
    
    