def GetTextUser(message):
    text = ""
    typeMessage = message["type"]

    if typeMessage == "text":
        text = (message["text"])["body"]
    elif typeMessage == "interactive":
        interactiveObject = message["interactive"]
        typeInteractive = interactiveObject["type"]

        if typeInteractive == "button_reply":
            text = (interactiveObject["button_reply"])["title"]
        elif typeInteractive == "list_reply":
            text = (interactiveObject["list_reply"])["title"]
        else:
            print("sin mensaje")
    else:
        print("sin mensaje")

    return text


def TextMessage(text, number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    return data


def TextFormatMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": "*Hola usuario* \n_Hola usuario_ \n~Hola usuario~ \n```Hola usuario```"
        }
    }
    return data


def ImageMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "image",
        "image": {
            "link": "https://static.wikia.nocookie.net/bokunoheroacademia/images/a/ac/Izuku_Midoriya_Traje_de_h%C3%A9roe_2.png/revision/latest/scale-to-width-down/224?cb=20180128234629&path-prefix=es"
        }
    }
    return data


def AudioMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "audio",
        "audio": {
            "link": "https://samplelib.com/lib/preview/mp3/sample-3s.mp3"
        }
    }
    return data


def VideoMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "video",
        "video": {
            "link": "https://samplelib.com/lib/preview/mp4/sample-10s.mp4",
            "caption": "Mi video"
        }
    }
    return data


def DocumentMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "document",
        "document": {
            "link": "https://www.wipo.int/edocs/pubdocs/es/wipo_pub_1055_exec_summary.pdf",
            "filename": "Artificial Intelligence",
            "caption": "Informe en pdf"
        }
    }
    return data


def LocationMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "location",
        "location": {
            "latitude": "-12.070958579029659",
            "longitude": "-77.03533752684365",
            "name": "Estadio Nacional del Peru",
            "address": "Jirón Madre de Dios S/N, Lima 15046"
        }
    }
    return data


def ButtonsMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Do you already have an account?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "001",
                            "title": "Sign up"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "002",
                            "title": "Log in"
                        }
                    }
                ]
            }
        }
    }
    return data


def ListMessage(number):
    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": "✅ I have these options"
            },
            "footer": {
                "text": "Select an option"
            },
            "action": {
                "button": "See options",
                "sections": [
                    {
                        "title": "Buy and sell products",
                        "rows": [
                            {
                                "id": "main-buy",
                                "title": "Buy",
                                "description": "Buy the best product your home"
                            },
                            {
                                "id": "main-sell",
                                "title": "Sell",
                                "description": "Sell your products"
                            }
                        ]
                    },
                    {
                        "title": "📍center of attention",
                        "rows": [
                            {
                                "id": "main-agency",
                                "title": "Agency",
                                "description": "Your can visit our agency"
                            },
                            {
                                "id": "main-contact",
                                "title": "Contact center",
                                "description": "One of our agents will assist you"
                            }
                        ]
                    }
                ]
            }
        }
    }
    return data
