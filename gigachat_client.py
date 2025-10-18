import requests
import uuid
import time
import json
from dotenv import load_dotenv
import os
from prompts import EXTRACT_MATERIAL_PROMPT, OBJECT_QUESTION_PROMPT

load_dotenv()

class GigaChatClient:
    def __init__(self):
        self.auth_url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        self.api_url = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'
        self.access_token = None
        self.token_expiration_time = None

    def get_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {os.getenv('KEY')}'
        }
        
        data = 'scope=GIGACHAT_API_PERS'
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=data, verify=False)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            self.token_expiration_time = time.time() + (token_data['expires_at'] / 1000) - 60
            
            return token_data
        except Exception as e:
            print(f"Ошибка получения токена: {e}")
            return None

    def _is_token_valid(self):
        if not self.access_token or not self.token_expiration_time:
            return False
        return time.time() < self.token_expiration_time

    def _ensure_valid_token(self):
        if not self._is_token_valid():
            return self.get_token()
        return True

    def generate(self, text):
        if not self._ensure_valid_token():
            return "Ошибка: не удалось получить токен"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": text}],
            "stream": False,
            "repetition_penalty": 1,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
            
            if response.status_code == 401:
                print("Токен истек, обновляем...")
                if self.get_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
                else:
                    return "Ошибка: не удалось обновить токен"
            
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"Ошибка генерации: {e}"

    def extract_material_info(self, text):
        if not self._ensure_valid_token():
            return {"error": "Не удалось получить токен"}
        
        prompt = EXTRACT_MATERIAL_PROMPT + text
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "repetition_penalty": 1,
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
            
            if response.status_code == 401:
                if self.get_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
                else:
                    return {"error": "Не удалось обновить токен"}
            
            response.raise_for_status()
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "Наименование материала": "Неизвестно",
                    "Количество материала": "Неизвестно", 
                    "Размер": "",
                    "Объем": "",
                    "Нетто": ""
                }
                
        except Exception as e:
            return {"error": f"Ошибка извлечения: {e}"}

    def answer_object_question(self, object_id, token, question):
        from api import get_object_info
        
        object_info = get_object_info(token, object_id)
        
        if "error" in object_info:
            return {"error": object_info["error"]}
        
        prompt = OBJECT_QUESTION_PROMPT.format(
            question=question,
            object_info=json.dumps(object_info, ensure_ascii=False, indent=2)
        )
        
        if not self._ensure_valid_token():
            return {"error": "Не удалось получить токен"}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "repetition_penalty": 1,
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
            
            if response.status_code == 401:
                if self.get_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
                else:
                    return {"error": "Не удалось обновить токен"}
            
            response.raise_for_status()
            result = response.json()
            return {"answer": result['choices'][0]['message']['content']}
            
        except Exception as e:
            return {"error": f"Ошибка генерации ответа: {e}"}

