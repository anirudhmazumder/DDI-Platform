from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os

app = FastAPI()

# Model path
MODEL_PATH = "/Users/masudip/Library/Application Support/nomic.ai/GPT4All/Llama-3.2-1B-Instruct-Q4_0.gguf"

# Load the model globally
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

llm = Llama(model_path=MODEL_PATH)

class RequestBody(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"message": "Llama model server is running!"}

class RequestBody(BaseModel):
    prompt: str
    max_tokens: int = 200
    temperature: float = 0.3

@app.post("/generate/")
def generate_text(request: RequestBody):
    if not llm:
        raise HTTPException(status_code=500, detail="Model not loaded.")
    print(f"Received request: {request.prompt}")
    response = llm(request.prompt, max_tokens=request.max_tokens, temperature=request.temperature)
    print(response)
    return {"response": response['choices'][0]['text'].strip()}
