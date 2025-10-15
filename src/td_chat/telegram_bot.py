import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from src.td_chat.main import run as run_crew_agent
import telegram.constants
from typing import List

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtiene el token del bot de las variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Límite de caracteres por mensaje de Telegram
MAX_MESSAGE_LENGTH = 4096

def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Divide un mensaje largo en múltiples mensajes respetando el límite de Telegram.
    Intenta dividir por saltos de línea para mantener la coherencia.
    """
    if len(text) <= max_length:
        return [text]

    messages = []
    current_message = ""

    # Dividir por líneas para mantener coherencia
    lines = text.split('\n')

    for line in lines:
        # Si una sola línea es más larga que el límite, dividirla por caracteres
        if len(line) > max_length:
            # Si hay contenido acumulado, guardarlo primero
            if current_message:
                messages.append(current_message)
                current_message = ""

            # Dividir la línea larga en chunks
            for i in range(0, len(line), max_length):
                messages.append(line[i:i + max_length])
            continue

        # Si agregar esta línea excede el límite, guardar el mensaje actual y empezar uno nuevo
        if len(current_message) + len(line) + 1 > max_length:
            messages.append(current_message)
            current_message = line
        else:
            # Agregar la línea al mensaje actual
            if current_message:
                current_message += '\n' + line
            else:
                current_message = line

    # Agregar el último mensaje si existe
    if current_message:
        messages.append(current_message)

    return messages

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida cuando se ejecuta el comando /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! Soy tu agente de CrewAI. Envíame un mensaje y trataré de responder.\n\n"
        f"Comandos disponibles:\n"
        f"/start - Mensaje de bienvenida\n"
        f"/clear - Limpiar historial de conversación",
    )

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Limpia el historial de conversación del usuario."""
    if 'chat_history' in context.chat_data:
        context.chat_data['chat_history'] = []
    await update.message.reply_text(
        "✓ Historial de conversación limpiado. Puedes comenzar una nueva conversación desde cero."
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

        # Log para debug
        print(f"Historial actual: {len(chat_history_list)} mensajes")

        # Ejecuta el agente de CrewAI
        agent_response = run_crew_agent(user_message, "\n".join(chat_history_list))

        # Actualiza el historial de chat
        chat_history_list.append(f"User: {user_message}")
        chat_history_list.append(f"Assistant: {agent_response}")

        # Mantiene solo los últimos 4 mensajes (2 turnos)
        # Esto mantiene un contexto reciente sin saturar el límite de tokens del LLM
        if len(chat_history_list) > 4:
            chat_history_list = chat_history_list[-4:]

        context.chat_data['chat_history'] = chat_history_list

        # Divide el mensaje si es muy largo y envía en múltiples partes
        response_text = str(agent_response)
        message_parts = split_message(response_text)

        print(f"Respuesta dividida en {len(message_parts)} mensajes")

        # Envía cada parte del mensaje
        for i, part in enumerate(message_parts):
            await update.message.reply_text(text=part)
            # Si hay más mensajes por enviar, espera un poco para no saturar
            if i < len(message_parts) - 1:
                await asyncio.sleep(0.5)

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
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("El bot se ha iniciado.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    main()