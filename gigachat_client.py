import os
import uuid
import base64
import requests
import json
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class GigaChatClient:
    def __init__(self):
        self.client_id = os.getenv('GIGACHAT_CLIENT_ID')
        self.client_secret = os.getenv('GIGACHAT_CLIENT_SECRET')
        self.basic_override = os.getenv('GIGACHAT_BASIC_AUTH')
        self.scopes = os.getenv('GIGACHAT_SCOPES', 'GIGACHAT_API_PERS')
        self.chat_base = 'https://gigachat.devices.sberbank.ru'
        self.token_url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        self.token = None
    
    def _build_basic_auth(self) -> str:
        if self.basic_override:
            return self.basic_override
        secret = self.client_secret or ''
        try:
            decoded = base64.b64decode(secret).decode('utf-8')
            if ':' in decoded:
                return secret
        except Exception:
            pass
        raw = f"{self.client_id}:{secret}"
        return base64.b64encode(raw.encode()).decode()
    
    def _get_token(self) -> str:
        if self.token:
            return self.token
        auth_b64 = self._build_basic_auth()
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4())
        }
        data = {'scope': self.scopes, 'grant_type': 'client_credentials'}
        response = requests.post(self.token_url, headers=headers, data=data, timeout=30, verify=False)
        response.raise_for_status()
        self.token = response.json()['access_token']
        return self.token
    
    def generate(self, prompt: str) -> str:
        token = self._get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            'model': 'GigaChat',
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False,
            'repetition_penalty': 1
        }
        response = requests.post(
            f'{self.chat_base}/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=60,
            verify=False
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    def _is_valid_material_json(self, data: Any) -> bool:
        keys = ["Наименование материала", "Количество материала", "Размер", "Объем", "Нетто"]
        if not isinstance(data, dict):
            return False
        for k in keys:
            if k not in data:
                return False
            v = data[k]
            if v is None:
                continue
            if not isinstance(v, str):
                return False
        return True
    
    def extract_material_info(self, text: str) -> str:
        base_prompt = (
            "Извлеки из текста информацию о материалах и верни только валидный JSON. "
            "Строго выведи один объект JSON с ключами: "
            "\"Наименование материала\", \"Количество материала\", \"Размер\", \"Объем\", \"Нетто\". "
            "Если материалов несколько, выбери ПЕРВЫЙ по порядку упоминания в тексте. "
            "Значения должны быть строками. Если значение не найдено, ставь пустую строку. "
            "Никакого текста вне JSON, без комментариев и без форматирования в код-блоках. "
            "Пример формы ответа: {\"Наименование материала\": \"\", \"Количество материала\": \"\", \"Размер\": \"\", \"Объем\": \"\", \"Нетто\": \"\"}. "
            "Текст: " + text
        )
        for _ in range(10):
            raw = self.generate(base_prompt).strip()
            if raw.startswith('```') and raw.endswith('```'):
                raw = raw.strip('`')
                parts = raw.split('\n', 1)
                raw = parts[1] if len(parts) > 1 else ''
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list) and len(parsed) > 0:
                    parsed = parsed[0]
                if self._is_valid_material_json(parsed):
                    return json.dumps(parsed, ensure_ascii=False)
            except Exception:
                pass
        return "Не удалось сформировать JSON"
