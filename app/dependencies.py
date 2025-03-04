from pinecone import Pinecone
from app.config import PC_KEY

index = Pinecone(api_key=PC_KEY).Index("ai-law")