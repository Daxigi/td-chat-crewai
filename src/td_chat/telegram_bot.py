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
        # Muestra un mensaje de "escribiendo..." para mejorar la experiencia del usuario
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.constants.ChatAction.TYPING)

        # Ejecuta el agente de CrewAI con el mensaje del usuario
        agent_response = run_crew_agent(user_message)

        # Envía la respuesta usando el modo de formato MARKDOWN (versión 1).
        await update.message.reply_text(
            text=str(agent_response),
            parse_mode=telegram.constants.ParseMode.MARKDOWN
        )

    except Exception as e:
        # Para mensajes de error, es mejor enviarlos como texto plano sin formato.
        error_message = f"Ocurrió un error al procesar tu solicitud: {e}"
        print(f"Error: {error_message}")
        await update.message.reply_text(text=error_message)

def main() -> None:
    """Inicia el bot de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: La variable de entorno TELEGRAM_BOT_TOKEN no fue encontrada.")
        return

    # Crea la aplicación del bot con el token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Asigna los manejadores de comandos y mensajes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Inicia el bot para que escuche nuevas actualizaciones.
    # Se añade stop_signals=None para evitar el error al correr en un hilo secundario.
    print("El bot se ha iniciado.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    main()