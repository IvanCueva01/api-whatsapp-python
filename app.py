from flask import Flask, request
import util
import whatsappservice
from openaiservice import GetAIResponse
from db import save_message

app = Flask(__name__)


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
    # check for specific keywords first
    if "hi" in text or "option" in text:
        data = util.TextMessage("Hello, how can i help you", number)
        dataMenu = util.ListMessage(number)
        listData.append(data)
        listData.append(dataMenu)
    elif "thanks" in text:
        data = util.TextMessage("Thank you for contacting us!", number)
        listData.append(data)
    elif "contact" in text:
        data = util.TextMessage(
            "*Contact center:* \n_+51 987 654 321_", number)
        listData.append(data)
    else:
        # Use AI for humanized responses
        ai_response = GetAIResponse(
            f"User message:{text}\nBusiness context: Provide a helpful response related to our services.")
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


if (__name__ == "__main__"):
    app.run()
