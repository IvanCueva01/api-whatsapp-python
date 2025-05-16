import openai

# Configure OpenAI API Key
OPEN_API_KEY = "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"

client = openai.OpenAI(api_key=OPEN_API_KEY)

with open("training_doc.txt", "r", encoding="utf-8") as f:
    business_context = f.read()


def GetAIResponse(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un asistente amigable y útil. Usa solo la siguiente información para responder: {business_context}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        print(f"AI response: {response.choices[0].message.content.strip()}")
        # Check if the response is empty
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        print(f"Error with AI response: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."
