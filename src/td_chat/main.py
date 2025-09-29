#!/usr/bin/env python
from td_chat.crew import TdChatCrew
import time

def run(user_question: str, chat_history: str):
    """
    Ejecuta la Crew con la pregunta del usuario y el historial del chat.
    """
    inputs = {
        'user_question': user_question,
        'chat_history': chat_history
    }
    
    try:
        # Instancia la clase de la Crew, llama al método crew() para obtener el objeto Crew,
        # y luego ejecuta el kickoff.
        print("--- Iniciando ejecución de la crew ---")
        start_time = time.time()
        result = TdChatCrew().crew().kickoff(inputs=inputs)
        end_time = time.time()
        print(f"--- Ejecución de la crew finalizada en {end_time - start_time:.2f} segundos ---")
        return result
    except Exception as e:
        # Es una buena práctica imprimir el error para depuración
        print(f"Error al ejecutar la crew: {e}")
        raise