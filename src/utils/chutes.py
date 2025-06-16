import os
import dotenv
import requests

dotenv.load_dotenv()

class ChutesManager:
    def __init__(self):
        self.api_key = os.getenv('CHUTES_API_KEY')

    def embed(self, prompt: str) -> dict:
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        
        body = {
            "inputs": prompt
        }

        response = requests.post(
            "https://chutes-baai-bge-large-en-v1-5.chutes.ai/embed",
            headers=headers,
            json=body
        )

        return response.json()
