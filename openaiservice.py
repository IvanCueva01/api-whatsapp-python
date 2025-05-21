import os
import json
import openai
from dotenv import load_dotenv
import numpy as np
import faiss
from db_utils import get_recent_messages

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

idx = faiss.read_index("faiss.index")
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

CONTACT_INFO_MESSAGE = "\n\nPuedes agendar una reunión con un asesor aquí: https://meetings.hubspot.com/angel40 o contactarnos al +51980092619."


def GetAIResponse(user_question, user_id, explicitly_requests_contact=False):
    try:
        # Guardar mensaje del usuario (This is handled in app.py)
        # save_message(user_id, "user", user_question)

        # recuperar contexto RAG
        user_emb = client.embeddings.create(
            input=user_question, model="text-embedding-ada-002").data[0].embedding
        D, I = idx.search(np.array([user_emb], dtype='float32'), k=3)
        retrieved = [chunks[i]for i in I[0]]

        # Historial de conversacion reciente
        history = get_recent_messages(user_id)

        # mensaje system
        system_prompt_content = (
            "Eres el asistente de BRCO para conectividad M2M. "
            "Responde usando sólo la información proporcionada en el contexto RAG y el historial de conversación, "
            "manteniendo un tono profesional y empático. Sé conciso y directo al punto."
        )

        user_question_lower = user_question.lower()
        requests_phone_specifically = any(keyword in user_question_lower for keyword in [
                                          "número", "teléfono", "llamar", "contacto directo"])

        if explicitly_requests_contact:
            if requests_phone_specifically and not any(keyword in user_question_lower for keyword in ["reunión", "agendar", "link", "enlace"]):
                # User primarily wants the phone number
                system_prompt_content += (
                    " El usuario ha solicitado explícitamente el número de contacto de un asesor. "
                    "Proporciona el número de contacto del asesor: +51980092619. "
                    "Finaliza tu respuesta con: 'El asesor estará esperando su llamada.'"
                )
            else:
                # User wants to schedule or is open to link and/or phone
                system_prompt_content += (
                    " El usuario ha solicitado explícitamente información de contacto o agendar una reunión. "
                    "Debes proporcionar SIEMPRE AMBOS: el enlace para agendar una reunión (https://meetings.hubspot.com/angel40) Y el número de contacto del asesor (+51980092619). "
                    "Integra esta información de forma natural y clara en tu respuesta. Si el usuario mencionó 'reunión' o 'agendar', puedes añadir al final: 'Si logras agendar, avísame para confirmar.' "
                )
        else:
            system_prompt_content += (
                " NO DEBES incluir información de contacto como números de teléfono o enlaces para agendar reuniones en tu respuesta. No ofrezcas proactivamente agendar una reunión o llamar a un asesor. "
                "En lugar de eso, después de responder directamente a la pregunta del usuario, finaliza tu mensaje preguntando si tiene alguna otra consulta o si desea más detalles sobre lo discutido. "
                "Por ejemplo, podrías preguntar: '¿Hay algo más en lo que te pueda ayudar sobre esto?' o '¿Te gustaría profundizar en algún aspecto?' o 'Si estás interesado en dar el siguiente paso, házmelo saber.'"
            )

        system_prompt = {
            "role": "system",
            "content": system_prompt_content
        }

        # Contexto (RAG)
        rag_context = [{
            "role": "user",
            "content": f"[Contexto de soporte M2M]\n{chunk}"
        } for chunk in retrieved]

        # combinar mensajes: system + historial + contexto + ultima pregunta
        messages = [system_prompt] + history + rag_context + \
            [{"role": "user", "content": user_question}]

        # llamada al modelo
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=500,
        )
        # Guardar respuesta del modelo
        answer = response.choices[0].message.content.strip()

        # Guardar respuesta del modelo (This is handled in app.py)
        # save_message(user_id, "assistant", answer)

        # Fallback logic refinement
        if explicitly_requests_contact:
            contains_link = "meetings.hubspot.com/angel40" in answer
            contains_phone = "+51980092619" in answer or "980 092 619" in answer

            if requests_phone_specifically and not any(keyword in user_question_lower for keyword in ["reunión", "agendar", "link", "enlace"]):
                if not contains_phone:
                    answer += "Puedes contactarnos al +51980092619. El asesor estará esperando su llamada."
            elif not (contains_link and contains_phone):
                # If general request and it missed one or both
                missing_info = []
                if not contains_link:
                    missing_info.append(
                        "Puedes agendar una reunión aquí: https://meetings.hubspot.com/angel40")
                if not contains_phone:
                    missing_info.append("o contactarnos al +51980092619")
                if missing_info:
                    answer += " " + " ".join(missing_info) + "."
                    if contains_link and not contains_phone:  # If it gave link but not phone
                        answer += " Si prefieres, también puedes contactarnos por teléfono."
                    elif not contains_link and contains_phone:  # If it gave phone but not link
                        answer += " Si lo deseas, también puedes agendar una reunión directamente."

        print(f"AI response: {answer}")
        return answer if answer else "Lo siento, no pude encontrar una respuesta adecuada a tu pregunta."
    except openai.OpenAIError as e:
        print(f"Error with AI response: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."
