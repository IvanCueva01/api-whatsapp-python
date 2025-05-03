import openai

# Configure OpenAI API Key
OPEN_API_KEY = "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"

client = openai.OpenAI(api_key=OPEN_API_KEY)


def GetAIResponse(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente amigable y útil."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        print(f"Error with AI response: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."
