import openai
import json
import numpy as np
import faiss

# Configure OpenAI API Key
OPEN_API_KEY = "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"

client = openai.OpenAI(api_key=OPEN_API_KEY)

with open("model.json", "r", encoding="utf-8") as f:
    data = json.load(f)

qa_pairs = []
for intent in data["intents"]:
    for pattern in intent["patterns"]:
        qa_pairs.append({
            "tag": intent["tag"],
            "pattern": pattern,
            "response": intent["responses"][0]
        })


def get_embedding(text: str):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


# crear indice faiss
embeddings = np.array([get_embedding(q["pattern"])
                      for q in qa_pairs]).astype("float32")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)


def search_answer(user_question):
    emb_user = np.array(get_embedding(user_question)
                        ).astype("float32").reshape(1, -1)

    D, I = index.search(emb_user, k=1)
    idx = I[0][0]
    similitud = D[0][0]

    return qa_pairs[idx]["response"] if similitud < 1.0 else "Lo siento, no pude encontrar una respuesta adecuada."


def GetAIResponse(user_question, context_response):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": (
                     "Eres un asistente amigable y útil para BRCO. "
                     "No inicies la conversación con saludos como 'Hola' ni repitas mensajes introductorios. "
                     "Responde directamente a la consulta del usuario utilizando solo la siguiente información: "
                     f"{context_response}. "
                     "Mantén tus respuestas en máximo 2 líneas. "
                     "Si necesitas dar contexto o ejemplos, usa máximo 5 líneas. "
                     "Si detectas que el usuario está interesado en el servicio, y escribe 'sí me gustaría' o 'estoy interesado', invítalo cordialmente a agendar una reunión en este enlace: "
                     "https://meetings.hubspot.com/angel40. "
                     "Si ves que desea comunicarse directamente con un asesor, envíale un mensaje con la información de contacto que es +51 980 092 619."
                 )
                 },
                {"role": "user", "content": user_question}
            ]
        )
        print(f"AI response: {response.choices[0].message.content.strip()}")
        # Check if the response is empty
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        print(f"Error with AI response: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."
