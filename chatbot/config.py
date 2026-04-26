from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from qdrant_client import QdrantClient

from sentence_transformers import CrossEncoder

from dotenv import load_dotenv

import subprocess

import os

load_dotenv()

url = os.getenv("QDRANT_URL")
qdrant_api = os.getenv("QDRANT_API")

def check_gpu():
    try:
        subprocess.check_output('nvidia-smi')
        return "cuda"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "cpu"

def embedding_model():
    embedding = OpenAIEmbeddings(
        model='text-embedding-3-small',
    )
    return embedding

def model_llm(temperature=0.7):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    return llm

def rerank_model():
    device_used=check_gpu()
    rerank = CrossEncoder(
        "Qwen/Qwen3-Reranker-0.6B", 
        device=device_used, 
        cache_folder="chatbot/model",
        local_files_only=True
    )
    return rerank

def qdrant_client():
    client = QdrantClient(
        url=url,
        api_key=os.getenv("QDRANT_API")
    )
    return client

def retrive_rag(embedding):
    retrive = QdrantVectorStore.from_existing_collection(
        embedding=embedding,
        url=url,
        api_key=os.getenv("QDRANT_API"),
        collection_name="Data_IMDB"
    )
    return retrive