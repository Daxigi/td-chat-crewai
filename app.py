#!/usr/bin/env python
from fastapi import FastAPI
from src.td_chat.main import run  # Importa la función run
from dotenv import load_dotenv

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
    try:
        result = run(request.question)  # Pasa la pregunta a la función run
        return {"status": "Crew run completed", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
