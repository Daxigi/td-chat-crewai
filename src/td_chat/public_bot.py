import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from td_chat.crew import PublicCrew
import telegram.constants
from typing import List
from datetime import datetime

# Carga las variables de entorno
load_dotenv()

# TOKEN DEL BOT PÚBLICO
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_VECINO")

# Límite de caracteres por mensaje de Telegram
MAX_MESSAGE_LENGTH = 4096

def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """Divide un mensaje largo en múltiples partes."""
    if len(text) <= max_length:
        return [text]
    messages = []
    current_message = ""
    lines = text.split('\n')
    for line in lines:
        if len(line) > max_length:
            if current_message:
                messages.append(current_message)
                current_message = ""
            for i in range(0, len(line), max_length):
                messages.append(line[i:i + max_length])
            continue
        if len(current_message) + len(line) + 1 > max_length:
            messages.append(current_message)
            current_message = line
        else:
            if current_message:
                current_message += '\n' + line
            else:
                current_message = line
    if current_message:
        messages.append(current_message)
    return messages

def run_public_agent(user_question: str, chat_history: List[str] = None, status_update_func=None):
    """Ejecuta el Crew del agente público."""
    if chat_history:
        formatted_history = "\n".join(chat_history)
    else:
        formatted_history = "No hay contexto previo."

    inputs = {
        'topic': 'Municipal Procedures',
        'current_year': str(datetime.now().year),
        'user_question': user_question,
        'chat_history': formatted_history
    }
    
    try:
        crew_instance = PublicCrew()
        
        if status_update_func:
            def sync_callback(step_output):
                try:
                    if isinstance(step_output, dict):
                        thought = step_output.get('thought', '')
                        tool = step_output.get('tool', '')
                    else:
                        thought = getattr(step_output, 'thought', '')
                        tool = getattr(step_output, 'tool', '')

                    message = ""
                    if tool and tool != "None":
                        message = f"Consultando guía: {tool}..."
                    elif thought:
                        message = "Buscando información..."
                    
                    if message:
                        status_update_func(message)     
                except Exception as e:
                    print(f"Error callback: {e}")
            
            crew_instance.step_callback = sync_callback

        result = crew_instance.crew().kickoff(inputs=inputs)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Error al procesar solicitud: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bienvenida del bot público."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 ¡Hola {user.mention_html()}! Soy el Asistente Virtual de Trámites Municipales.\n\n"
        f"Puedo informarte sobre:\n"
        f"📄 Requisitos para trámites\n"
        f"📅 Plazos y vencimientos\n"
        f"📍 Lugares de atención\n\n"
        f"¿En qué puedo ayudarte hoy?"
    )

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'chat_history' in context.chat_data:
        context.chat_data['chat_history'] = []
    await update.message.reply_text("✓ Conversación reiniciada.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejo de mensajes del bot público."""
    user_message = update.message.text
    print(f"[Public Bot] Mensaje de {update.effective_user.full_name}: {user_message}")

    try:
        status_message = await update.message.reply_text("⏳ Buscando información...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.constants.ChatAction.TYPING)

        if 'chat_history' not in context.chat_data:
            context.chat_data['chat_history'] = []
        chat_history_list = context.chat_data['chat_history']

        loop = asyncio.get_running_loop()
        
        def on_status_update(message_text):
            async def update_telegram_msg():
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        text=f"⏳ {message_text}"
                    )
                except Exception:
                    pass
            asyncio.run_coroutine_threadsafe(update_telegram_msg(), loop)

        # Ejecución asíncrona del agente
        agent_response = await loop.run_in_executor(
            None, 
            lambda: run_public_agent(user_message, chat_history=chat_history_list, status_update_func=on_status_update)
        )

        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        except Exception:
            pass

        chat_history_list.append(f"User: {user_message}")
        chat_history_list.append(f"Assistant: {agent_response}")
        if len(chat_history_list) > 4:
            context.chat_data['chat_history'] = chat_history_list[-4:]

        message_parts = split_message(str(agent_response))
        for i, part in enumerate(message_parts):
            await update.message.reply_text(text=part)
            if i < len(message_parts) - 1:
                await asyncio.sleep(0.5)

    except Exception as e:
        await update.message.reply_text(f"Lo siento, tuve un problema técnico: {e}")

def main() -> None: 
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: Falta la variable TELEGRAM_BOT_TOKEN_VECINO en el archivo .env")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("🤖 Bot Público de Trámites iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    main()
