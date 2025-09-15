import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from src.td_chat.main import run as run_crew_agent
import telegram.constants
import re

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def escape_markdown_v2(text: str) -> str:
    """Helper function to escape characters in MarkdownV2."""
    # List of characters to escape in MarkdownV2
    # See https://core.telegram.org/bots/api#markdownv2-style
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your CrewAI agent. Send me a message and I'll try to answer.",
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user_message = update.message.text
    print(f"Received message from {update.effective_user.full_name}: {user_message}")
    
    try:
        # Run the CrewAI agent with the user's message
        agent_response = run_crew_agent(user_message)
        # Escape special characters first
        escaped_response = escape_markdown_v2(str(agent_response))
        # Replace single newlines with two spaces and a newline for MarkdownV2 line breaks
        formatted_response = escaped_response.replace('\n', '  \n')
        await update.message.reply_text(formatted_response, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    except Exception as e:
        # For error messages, escape them as well
        error_message = f"An error occurred while processing your request: {e}"
        await update.message.reply_text(escape_markdown_v2(error_message), parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    print("Bot started. Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=False)

if __name__ == "__main__":
    main()
