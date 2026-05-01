from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase

from qdrant_client import QdrantClient

from sentence_transformers import CrossEncoder

from dotenv import load_dotenv

import subprocess

import os

load_dotenv()

url = os.getenv("QDRANT_URL")
qdrant_api = os.getenv("QDRANT_API")
url_omdb = os.getenv("OMDb_url")
OMDB_API = os.getenv("OMDb_api_key")

def check_gpu():
    try:
        subprocess.check_output('nvidia-smi')
        return "cuda"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "cpu"
    
embedding = OpenAIEmbeddings(
    model='text-embedding-3-small',
)

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

client = QdrantClient(
    url=url,
    api_key=os.getenv("QDRANT_API")
)

retrive = QdrantVectorStore.from_existing_collection(
    embedding=embedding,
    url=url,
    api_key=os.getenv("QDRANT_API"),
    collection_name="Data_IMDB"
)

db_engine = create_engine("sqllite/////home/hasyim/projects-ai-engineer/Capston3/chatbot/data/process/IMDB_FILM_capston3.db")
db = SQLDatabase(db_engine)