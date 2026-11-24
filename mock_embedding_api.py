from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import random
import uvicorn
import asyncio

TIMEOUT_VALUE = 5

class EmbeddingRequest(BaseModel):
    input: str
    
class EmbeddingResponse(BaseModel):
    embedding: list[float]
    
app = FastAPI()
@app.post("/embed")
async def calculate_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    if "test_429" in request.input:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    elif "test_500" in request.input:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    elif "test_503" in request.input:
        raise HTTPException(status_code=503, detail="Service Unavailable")
    elif "test_timeout" in request.input:
        await asyncio.sleep(TIMEOUT_VALUE)
    elif "test_400" in request.input:
        raise HTTPException(status_code=400, detail="Bad Request")
    elif "test_404" in request.input:
        raise HTTPException(status_code=404, detail="Not Found")
    elif "analysis" in request.input and random.random() <= 0.3:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    data = [random.random() for _ in range(128)]
    result = EmbeddingResponse(embedding=data)
    return result

if __name__ == "__main__":
    uvicorn.run("mock_embedding_api:app", host="127.0.0.1", port=8000, reload=True)