#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from typing import Optional, List

from td_chat.crew import TdChat

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run(user_question: str, chat_history: List[str] = None, status_update_func=None):
    """
    Run the crew using session-based context passed from the Telegram bot.
    :param status_update_func: Async function to send updates to the user (e.g., "Thinking...").
    """
    
    # Formatear el historial para el prompt
    if chat_history:
        formatted_history = "\n".join(chat_history)
    else:
        formatted_history = "No hay contexto previo."

    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year),
        'user_question': user_question,
        'chat_history': formatted_history
    }
    
    try:
        # Instanciamos el Crew
        crew_instance = TdChat()
        
        # Si nos pasaron una función de actualización (aunque sea dummy por ahora para probar),
        # se la asignamos al agente. 
        # NOTA: CrewAI ejecuta esto en un hilo bloqueante. Pasar funciones async de telegram aquí 
        # requiere manejo de loops (asyncio.run_coroutine_threadsafe).
        if status_update_func:
            # Definimos un wrapper síncrono que el agente pueda llamar
            def sync_callback(step_output):
                try:
                    # Intentar obtener tool y thought ya sea de objeto o dict
                    if isinstance(step_output, dict):
                        thought = step_output.get('thought', '')
                        tool = step_output.get('tool', '')
                    else:
                        thought = getattr(step_output, 'thought', '')
                        tool = getattr(step_output, 'tool', '')

                    message = ""
                    if tool and tool != "None":
                         # Si hay uso de herramienta, es prioritario mostrarlo
                        message = f"Busco información en: {tool}..."
                    elif thought:
                        # Si solo está pensando
                        message = "Analizando tu consulta..."
                    
                    if message:
                        status_update_func(message)
                        
                except Exception as e:
                    print(f"Error en callback de estado: {e}")
            
            crew_instance.step_callback = sync_callback

        # EJECUCIÓN: CrewAI
        result = crew_instance.crew().kickoff(inputs=inputs)
        return result

    except Exception as e:
        import traceback
        print("--- ERROR EN LA EJECUCIÓN DEL CREW ---")
        traceback.print_exc()
        print("------------------------------------")
        raise Exception(f"Ocurrió un error al procesar la solicitud: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year),
        'user_question': "Training mode",
        'chat_history': "Training context"
    }
    try:
        TdChat().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        TdChat().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year),
        'user_question': "Test mode",
        'chat_history': "Test context"
    }
    
    try:
        TdChat().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")