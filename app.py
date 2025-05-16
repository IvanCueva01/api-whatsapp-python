from flask import Flask, request
import util
import sqlite3
import whatsappservice
from openaiservice import GetAIResponse, search_answer
from db import get_connection
from db_setup import init_db


app = Flask(__name__)

init_db()


@app.route('/welcome', methods=['GET'])
def index():
    return "Welcome developer"


@app.route('/whatsapp', methods=['GET'])
def VerifyToken():
    try:
        accessToken = "FADSA89DD8AS9DADADSA9D9"
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token != None and challenge != None and token == accessToken:
            return challenge
        else:
            return "", 400
    except ValueError:
        return "", 400


@app.route('/whatsapp', methods=['POST'])
def ReceivedMessage():
    try:
        body = request.get_json()
        print(body)
        entry = (body["entry"])[0]
        changes = (entry["changes"])[0]
        value = changes["value"]
        message = (value["messages"])[0]
        number = message["from"]

        text = util.GetTextUser(message)
        ProcessMessage(text, number)
        print(text)

        return "EVENT_RECEIVED"
    except ValueError:
        return "EVENT_RECEIVED"


def ProcessMessage(text, number):

    text = text.lower()
    listData = []

    # Use AI for humanized responses
    answer_base = search_answer(text)
    ai_response = GetAIResponse(
        f"User message:{text}\nBusiness context: Provide a helpful response related to our services.", answer_base)
    data = util.TextMessage(ai_response, number)
    listData.append(data)

    save_message(number, text, ai_response)
    for item in listData:
        whatsappservice.SendMessageWhatsapp(item)

# Generate message is for testing


def GenerateMessage(text, number):

    text = text.lower()
    if "text" in text:
        data = util.TextMessage("Text", number)
    elif "format" in text:
        data = util.TextFormatMessage(number)
    elif "image" in text:
        data = util.ImageMessage(number)
    elif "video" in text:
        data = util.VideoMessage(number)
    elif "audio" in text:
        data = util.AudioMessage(number)
    elif "document" in text:
        data = util.DocumentMessage(number)
    elif "location" in text:
        data = util.LocationMessage(number)
    elif "button" in text:
        data = util.ButtonsMessage(number)
    elif "list" in text:
        data = util.ListMessage(number)
    else:
        data = None

    whatsappservice.SendMessageWhatsapp(data)


def save_message(user_number, user_message, bot_response):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_number, user_message, bot_response)
            VALUES (?, ?, ?)
        ''', (user_number, user_message, bot_response))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al guardar el mensaje: {e}")
    finally:
        conn.close()


if (__name__ == "__main__"):
    app.run()
