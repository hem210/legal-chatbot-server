import json
import httpx
from app.dependencies import index
from app.config import MAX_RET_DOCS, MAX_SCORE, HF_TOKEN

# -------- Code for Local Chroma DB based Retrieval -----------

# async def rag_service(query: str):
#     chromadb_path = os.path.abspath(os.path.join(os.getcwd(), 'db', 'main'))
#     client = chromadb.PersistentClient(path=chromadb_path)

#     # # # List all collections
#     # collections = client.list_collections()

#     # # Print the collection names
#     # for collection in collections:
#     #     print(f"Collection Name: {collection.name}")

#     # Assume 'collection_name' is the name of your collection in Chroma DB
#     collection_name = 'main'

#     emb_fn = embedding_functions.HuggingFaceEmbeddingFunction(api_key=HF_TOKEN, model_name="BAAI/bge-m3")
#     # Get the collection
#     collection = client.get_collection(name=collection_name)

#     query_emb = emb_fn([query])
#     print("query emb generated")
#     ctxt_docs = collection.query(query_embeddings=query_emb, n_results=10)
#     print("cntxt docs retrieved")

#     # print(ctxt_docs)

#     relevant_c = []
#     if ctxt_docs["distances"] is not None:
#         for i, distance in enumerate(ctxt_docs["distances"][0]):
#             if float(distance) <= 0.7:
#                 if ctxt_docs["documents"] is not None:
#                     relevant_c.append(ctxt_docs["documents"][0][i])

#     return relevant_c

async def rag_service(query: str):

    model_id = "BAAI/bge-m3"
    hf_token = HF_TOKEN

    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}

    payload = {
            "inputs": query,
            "options": {
                "wait_for_model": True
            }
        }

    print("[INFO] Generating query embedding...")
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, headers=headers, json=payload, timeout=6000)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response text:", response.text)
        else:
            try:
                # Print the result
                query_emb = response.json()
            except json.JSONDecodeError:
                print("Failed to decode JSON response")
                print("Response text:", response.text)

    query_emb = response.json()

    print("[INFO] Query embedding generated.")

    try:
        result = index.query(vector=query_emb, top_k=MAX_RET_DOCS, include_values=True, include_metadata=True)
    except Exception as e:
        print("Error in querying pinecone:", e)
    
    print("[INFO] Context documents retrieved.")
    relevant_c = []
    for match in result.matches:
        if match["score"] <= MAX_SCORE and match["metadata"]["question"] is not None and match["metadata"]["answer"] is not None:
            context = match["metadata"]["question"] + " " + match["metadata"]["answer"]
            relevant_c.append(context)

    return relevant_c
