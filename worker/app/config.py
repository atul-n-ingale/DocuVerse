import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/docuverse_worker")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "docuverse")
NLM_INGESTOR_URL = os.getenv("NLM_INGESTOR_URL", "")

# Validate required environment variables
if not PINECONE_API_KEY:
    print("WARNING: PINECONE_API_KEY is not set")
if not PINECONE_INDEX:
    print("WARNING: PINECONE_INDEX is not set, using default: docuverse")
if not NLM_INGESTOR_URL:
    print("WARNING: NLM_INGESTOR_URL is not set")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000/api")
