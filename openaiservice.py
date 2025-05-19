import openai
import json
import os
from dotenv import load_dotenv
import numpy as np
import faiss

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

idx = faiss.read_index("faiss.index")
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)


def GetAIResponse(user_question):
    try:
        # emb y retrieve
        user_emb = client.embeddings.create(
            input=user_question, model="text-embedding-ada-002").data[0].embedding
        D, I = idx.search(np.array([user_emb], dtype='float32'), k=3)
        retrieved = [chunks[i]for i in I[0]]
        # construir prompt
        system_prompt = (
            "Eres ABI el asistente de BRCO para conectividad M2M. "
            "Responde usando sólo la información proporcionada, "
            "manteniendo un tono profesional y empático."
        )
        user_prompt = "\n\n".join([
            "### Contexto:\n" + retrieved[0],
            retrieved[1],
            retrieved[2],
            "### Pregunta:\n" + user_question,
        ])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        answer = response.choices[0].message.content.strip()
        print(f"AI response: {response.choices[0].message.content.strip()}")
        # Check if the response is empty
        return answer if answer else "Lo siento, no pude encontrar una respuesta adecuada a tu pregunta."
    except openai.OpenAIError as e:
        print(f"Error with AI response: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."
