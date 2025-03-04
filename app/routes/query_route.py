from fastapi import APIRouter, Form
from app.config import HF_TOKEN
from app.services.rag_service import rag_service
from app.services.generate_prompt import generate_prompt
import httpx
import json

router = APIRouter()

@router.post("/query")
async def process_query(query: str = Form()):

    relevant_c = await rag_service(query)
    context = ""
    if len(relevant_c) > 0:
        context = context.join(relevant_c)
    else:
        return {"response": "Sorry but I don't have relevant knowledge to asnwer that query."}
    
    prompt = await generate_prompt(query, context)

    print("[INFO] Prompt generated.")

    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "contexts": context,
        "parameters": {
            "top_p": 0.40,
            "max_new_tokens": 2000,
            "temperature": 0.40,
        }
    }

    print("[INFO] Generating inference...")
    result = ""
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, headers=headers, json=payload, timeout=6000)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response text:", response.text)
        else:
            try:
                # Print the result
                result_json = response.json()
                result = result_json[0]["generated_text"]
                result = result.rpartition("Answer:")[-1].strip()
            except json.JSONDecodeError:
                print("Failed to decode JSON response")
                print("Response text:", response.text)
    # output = response.json()
    return {"response": result}
