from fastapi import FastAPI
from app.routes import query_route

app = FastAPI()
app.include_router(query_route.router)

@app.get("/")
async def read_root():
    return {"Hello": "World"}