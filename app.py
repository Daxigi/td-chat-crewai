#!/usr/bin/env python
from fastapi import FastAPI
from src.td_chat.main import run  # Importa la función run
from dotenv import load_dotenv
import time

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

from pydantic import BaseModel

class CrewRequest(BaseModel):
    question: str

@app.post("/run-crew")
def run_crew_endpoint(request: CrewRequest):
    start_time = time.time()
    try:
        result = run(request.question)
        end_time = time.time()
        execution_time = end_time - start_time
        return {
            "status": "Crew run completed",
            "result": result,
            "execution_time": f"{execution_time:.2f} seconds"
        }
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        return {
            "status": "error",
            "message": str(e),
            "execution_time": f"{execution_time:.2f} seconds"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)