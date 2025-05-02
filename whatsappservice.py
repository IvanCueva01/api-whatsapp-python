import requests
import json


def SendMessageWhatsapp(data):
    try:
        token = "EABuh9sCMyYwBOZCsOtS0ptLzmJli0YmbMc9fF0ezHovThJeZBwuVd668y99thrHxH2ZAfxZCW4V7LGmRsBeSeZCpS1LRltXWZAI4PZBYZAbYhtBgpMID6jQupOxIKefXvJJjkcQ1tg3uKLIA4RHCXXSZCPhEX0WE5FVZCnPCwse7QS7IGXc8axqZCIuEnB0wSjmuWTZChwaIscv3K98y6WRSrtbtQ0vi78jVNSXQDnIEhyhl"
        api_url = "https://graph.facebook.com/v22.0/638291076024157/messages"
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
