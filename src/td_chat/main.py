#!/usr/bin/env python
import sys
import warnings
from datetime import datetime

from td_chat.crew import TdChat
from mem0 import Memory

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Inicializamos Mem0
m = Memory()

def run(user_question: str, user_id: str = "default_user"):
    """
    Run the crew con memoria inteligente (Mem0).
    Maneja user_id inválidos y formatos de memoria mixtos (dict/str).
    """
    
    # --- BLOQUE DE SEGURIDAD: Validar user_id ---
    if not user_id or not isinstance(user_id, str):
        print(f"⚠️ Advertencia: user_id inválido recibido ({type(user_id)}). Usando 'usuario_generico'.")
        user_id = "usuario_generico"
    # --------------------------------------------

    print(f"🧠 Mem0: Buscando recuerdos para usuario '{user_id}'...")

    try:
        # 1. RECUPERACIÓN: Buscamos contexto previo
        related_memories = m.search(user_question, user_id=user_id, limit=5)
        
        history_text = ""
        if related_memories:
            # --- CORRECCIÓN DEL ERROR 'str object has no attribute get' ---
            formatted_memories = []
            for mem in related_memories:
                if isinstance(mem, dict):
                    # Si es diccionario, extraemos el campo 'memory' o el texto que tenga
                    formatted_memories.append(f"- {mem.get('memory', str(mem))}")
                else:
                    # Si es string (texto plano), lo usamos directamente
                    formatted_memories.append(f"- {mem}")
            
            history_text = "\n".join(formatted_memories)
            chat_history = f"Contexto recuperado de conversaciones anteriores:\n{history_text}"
            # --------------------------------------------------------------
        else:
            chat_history = "No hay contexto previo relevante para esta consulta."

        # 2. PREPARACIÓN: Inputs para el Crew
        inputs = {
            'topic': 'AI LLMs',
            'current_year': str(datetime.now().year),
            'user_question': user_question,
            'chat_history': chat_history
        }
        
        # 3. EJECUCIÓN: CrewAI
        result = TdChat().crew().kickoff(inputs=inputs)
        
        # 4. ALMACENAMIENTO: Guardamos la nueva interacción
        interaction_to_save = f"Usuario preguntó: '{user_question}' -> Asistente respondió: '{str(result)}'"
        m.add(interaction_to_save, user_id=user_id)
        
        return result

    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


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