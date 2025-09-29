import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from src.td_chat.main import run as run_crew_agent
import telegram.constants

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtiene el token del bot de las variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida cuando se ejecuta el comando /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! Soy tu agente de CrewAI. Envíame un mensaje y trataré de responder.",
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa el mensaje del usuario y devuelve la respuesta del agente."""
    user_message = update.message.text
    print(f"Mensaje recibido de {update.effective_user.full_name}: {user_message}")

    try:
        # Muestra un mensaje de "escribiendo..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.constants.ChatAction.TYPING)

        # Inicializa el historial de chat si no existe
        if 'chat_history' not in context.chat_data:
            context.chat_data['chat_history'] = []

        chat_history_list = context.chat_data['chat_history']

        # Ejecuta el agente de CrewAI
        agent_response = run_crew_agent(user_message, "\n".join(chat_history_list))

        # Actualiza el historial de chat
        chat_history_list.append(f"User: {user_message}")
        chat_history_list.append(f"Assistant: {agent_response}")

        # Mantiene solo los últimos 4 mensajes (2 turnos)
        if len(chat_history_list) > 4:
            chat_history_list = chat_history_list[-4:]
        
        context.chat_data['chat_history'] = chat_history_list

        # Envía la respuesta en texto plano
        await update.message.reply_text(
            text=str(agent_response)
        )

    except Exception as e:
        # Para mensajes de error, enviarlos como texto plano
        error_message = f"Ocurrió un error al procesar tu solicitud: {e}"
        print(f"Error: {error_message}")
        await update.message.reply_text(text=error_message)

def main() -> None:
    """Inicia el bot de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: La variable de entorno TELEGRAM_BOT_TOKEN no fue encontrada.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("El bot se ha iniciado.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    main()