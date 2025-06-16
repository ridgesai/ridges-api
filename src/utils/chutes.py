import os
import dotenv
import requests
import aiohttp
import json
from typing import Any

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
    
    async def inference(self, text_input: str, code_input: str, return_text: bool, return_code: bool, model: str = "deepseek-ai/DeepSeek-V3-0324"):
        if not model:
            model = "deepseek-ai/DeepSeek-V3-0324"
        
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        
        body = {
            "model": model,
            "messages": [],
            "stream": True,
            "max_tokens": 1024,
            "temperature": 0.7
        }

        if return_text and return_code:
            body['messages'].append({
                "role": "system",
                "content": "You MUST return a raw JSON object with two keys: 'text_response' and 'code_response'. Do not wrap it in markdown code blocks or add any formatting. The 'text_response' MUST contain your text response, and 'code_response' MUST contain your code response in diff format (VERY IMPORTANT THAT IT IS IN DIFF FORMAT). Format: {\"text_response\": \"your text here\", \"code_response\": \"your code diff here\"}"
            })
        elif return_text:
            body['messages'].append({
                "role": "system",
                "content": "You MUST return a raw JSON object with two keys: 'text_response' and 'code_response'. Do not wrap it in markdown code blocks or add any formatting. The 'text_response' MUST contain your text response, and 'code_response' MUST be empty. Format: {\"text_response\": \"your text here\", \"code_response\": \"\"}"
            })
        elif return_code:
            body['messages'].append({
                "role": "system",
                "content": "You MUST return a raw JSON object with two keys: 'text_response' and 'code_response'. Do not wrap it in markdown code blocks or add any formatting. The 'text_response' MUST be empty, and 'code_response' MUST contain your code response in diff format (VERY IMPORTANT THAT IT IS IN DIFF FORMAT). Format: {\"text_response\": \"\", \"code_response\": \"your code diff here\"}"
            })

        if text_input:
            body['messages'].append({
                "role": "user",
                "content": f"Here is the text input:\n\n{text_input}"
            })
        if code_input:
            body['messages'].append({
                "role": "user",
                "content": f"Here is the code input:\n\n```\n{code_input}\n```"
            })

        response_chunks = []
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.chutes.ai/v1/chat/completions", 
                headers=headers,
                json=body
            ) as response:
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = data.strip()
                            if json.loads(chunk)['choices'][0]['delta']['content']:
                                response_chunks.append(json.loads(chunk)['choices'][0]['delta']['content'])
                        except Exception as e:
                            print(f"Error parsing chunk: {e}")
        
        response_text = "".join(response_chunks)
        
        try:
            cleaned_response = response_text
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("```")[1]
            if cleaned_response.startswith("json"):
                cleaned_response = cleaned_response[4:]
            cleaned_response = cleaned_response.strip()
            cleaned_response_json = json.loads(cleaned_response)
            if "text_response" not in cleaned_response_json:
                raise Exception("text_response not found in response")
            if "code_response" not in cleaned_response_json:
                raise Exception("code_response not found in response")
            return {
                "text_response": cleaned_response_json["text_response"] if return_text else None,
                "code_response": cleaned_response_json["code_response"] if return_code else None
            }
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response")
