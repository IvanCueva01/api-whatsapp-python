import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def SendMessageWhatsapp(data):
    try:
        token = os.getenv("WHATSAPP_TOKEN")
        api_url = os.getenv("WHATSAPP_API_URL")
        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer " + token}
        response = requests.post(
            api_url, data=json.dumps(data), headers=headers, timeout=(5, 10))

        if response.status_code == 200:
            return True

        return False
    except requests.RequestException as exception:
        print(exception)
        return False
