import os
from telegram import Bot
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from dotenv import load_dotenv

load_dotenv()

class SendMessageInput(BaseModel):
    """Input for SendMessageTool."""
    message: str = Field(..., description="The message to send.")

class SendMessageTool(BaseTool):
    name: str = "send_telegram_message"
    description: str = "Sends a message to a Telegram chat."
    args_schema: Type[BaseModel] = SendMessageInput
    
    def _run(self, message: str) -> str:
        """Sends a message to a Telegram chat."""
        try:
            bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN_AGENTE"))
            bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=message)
            return "Message sent successfully."
        except Exception as e:
            return f"Error sending message: {e}"
