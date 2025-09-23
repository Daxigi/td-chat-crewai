import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from src.td_chat.main import run as run_crew_agent
import telegram.constants

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Gestor de historial de chat (en memoria)
chat_histories = {} 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    # Limpia el historial cuando el usuario inicia una nueva conversación
    if chat_id in chat_histories:
        del chat_histories[chat_id]
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! Soy tu agente de IA. ¿En qué puedo ayudarte hoy?"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_message = update.message.text
    # Recupera el historial de este chat o establece un valor inicial si no existe
    history = chat_histories.get(chat_id, "No hay historial previo.")

    try:
        # Muestra el indicador "escribiendo..."
        await context.bot.send_chat_action(chat_id=chat_id, action=telegram.constants.ChatAction.TYPING)
        
        # --- LLAMADA CORREGIDA ---
        # Llama a la función run con los dos argumentos requeridos
        agent_response = run_crew_agent(user_question=user_message, chat_history=history)
        
        # Limpieza de seguridad para la respuesta antes de enviarla
        clean_response = str(agent_response).replace('<br>', '\n').replace('<br/>', '\n')
        clean_response = clean_response.replace('&nbsp;', ' ')
        
        await update.message.reply_text(text=clean_response, parse_mode=telegram.constants.ParseMode.HTML)
        
        # Actualiza el historial con el nuevo turno de la conversación
        chat_histories[chat_id] = f"{history}\nHumano: {user_message}\nIA: {agent_response}\n"

    except Exception as e:
        error_message = f"Ocurrió un error al procesar tu solicitud: {e}"
        print(f"Error: {error_message}")
        await update.message.reply_text(text=error_message)

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("El bot se ha iniciado.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    main()