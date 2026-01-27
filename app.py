#!/usr/bin/env python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from td_chat.main import run  # Importa la función run
from dotenv import load_dotenv
import time
import threading
import asyncio
from td_chat.telegram_bot import main as run_telegram_bot

load_dotenv()

def start_telegram_bot_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_telegram_bot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run the Telegram bot in a separate thread
    telegram_thread = threading.Thread(target=start_telegram_bot_in_thread)
    telegram_thread.daemon = True  # Allow main program to exit
    telegram_thread.start()
    print("Telegram bot started in a separate thread.")
    yield
    # Shutdown: can be used to clean up resources
    print("Application shutting down.")

app = FastAPI(lifespan=lifespan)

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
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8765, 
        loop="asyncio"  
    )