import os
import uuid
import base64
import requests
import json
import logging
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GigaChatClient:
    def __init__(self):
        self.client_id = os.getenv('GIGACHAT_CLIENT_ID')
        self.client_secret = os.getenv('GIGACHAT_CLIENT_SECRET')
        self.basic_override = os.getenv('GIGACHAT_BASIC_AUTH')
        self.scopes = os.getenv('GIGACHAT_SCOPES', 'GIGACHAT_API_PERS')
        self.chat_base = 'https://gigachat.devices.sberbank.ru'
        self.token_url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        self.token = None
        self.token_expires_at = None
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 30
    
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
    
    def _is_token_valid(self) -> bool:
        if not self.token:
            return False
        if not self.token_expires_at:
            return True
        return time.time() < self.token_expires_at - 60
    
    def _get_token(self) -> str:
        if self._is_token_valid():
            logger.info("Using existing valid GigaChat token")
            return self.token
        
        logger.info("Requesting new GigaChat token...")
        auth_b64 = self._build_basic_auth()
        
        for attempt in range(self.max_retries):
            try:
                headers = {
                    'Authorization': f'Basic {auth_b64}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'RqUID': str(uuid.uuid4())
                }
                payload = {'scope': self.scopes}
                
                logger.info(f"Token request attempt {attempt + 1}/{self.max_retries}")
                logger.info(f"Making token request to: {self.token_url}")
                
                response = requests.post(
                    self.token_url, 
                    headers=headers, 
                    data=payload, 
                    timeout=self.timeout, 
                    verify=False
                )
                
                logger.info(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data['access_token']
                    if 'expires_at' in token_data:
                        self.token_expires_at = token_data['expires_at']
                    else:
                        self.token_expires_at = time.time() + 1800
                    logger.info("GigaChat token obtained successfully")
                    return self.token
                else:
                    logger.warning(f"Token request failed with status {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"Token request failed after {self.max_retries} attempts")
                        
            except requests.exceptions.Timeout:
                logger.warning(f"Token request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("Token request timeout after all retries")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Token request connection error on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("Token request connection error after all retries")
            except Exception as e:
                logger.error(f"Token request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise
        
        raise Exception("Failed to get token after all retries")
    
    def generate(self, prompt: str) -> str:
        logger.info(f"Generating response for prompt: {prompt[:100]}...")
        
        for attempt in range(self.max_retries):
            try:
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
                    'repetition_penalty': 1,
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
                
                logger.info(f"Generate request attempt {attempt + 1}/{self.max_retries}")
                logger.info(f"Making generate request to: {self.chat_base}/api/v1/chat/completions")
                
                response = requests.post(
                    f'{self.chat_base}/api/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                    verify=False
                )
                
                if response.status_code == 401:
                    logger.warning("Token expired, refreshing...")
                    self.token = None
                    self.token_expires_at = None
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise Exception("Token refresh failed after all retries")
                
                if response.status_code == 200:
                    result = response.json()['choices'][0]['message']['content']
                    logger.info("GigaChat generate response received successfully")
                    return result
                else:
                    logger.warning(f"Generate request failed with status {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"Generate request failed after {self.max_retries} attempts")
                
            except requests.exceptions.Timeout:
                logger.warning(f"Generate request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("Generate request timeout after all retries")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Generate request connection error on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("Generate request connection error after all retries")
            except Exception as e:
                logger.error(f"Generate request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise
        
        raise Exception("Failed to generate response after all retries")
    
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
        logger.info(f"Extracting material info from text: {text[:100]}...")
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
        
        for attempt in range(5):
            try:
                logger.info(f"Extract attempt {attempt + 1}/5")
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
                        logger.info("Material info extracted successfully")
                        return json.dumps(parsed, ensure_ascii=False)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed on attempt {attempt + 1}: {str(e)}")
                    if attempt < 4:
                        time.sleep(self.retry_delay)
                        continue
                except Exception as e:
                    logger.warning(f"Validation failed on attempt {attempt + 1}: {str(e)}")
                    if attempt < 4:
                        time.sleep(self.retry_delay)
                        continue
                        
            except Exception as e:
                logger.warning(f"Extract attempt {attempt + 1} failed: {str(e)}")
                if "timeout" in str(e).lower() or "connection" in str(e).lower():
                    if attempt < 4:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        break
                elif "401" in str(e) or "token" in str(e).lower():
                    self.token = None
                    self.token_expires_at = None
                    if attempt < 4:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        break
                else:
                    if attempt < 4:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        break
                
        logger.error("Failed to extract material info after 5 attempts")
        return json.dumps({
            "Наименование материала": "Неизвестно",
            "Количество материала": "Неизвестно", 
            "Размер": "",
            "Объем": "",
            "Нетто": ""
        }, ensure_ascii=False)
    
    def health_check(self) -> Dict[str, Any]:
        try:
            token = self._get_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(
                f'{self.chat_base}/api/v1/models',
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {"status": "healthy", "message": "GigaChat API доступен"}
            else:
                return {"status": "unhealthy", "message": f"GigaChat API недоступен: {response.status_code}"}
                
        except Exception as e:
            return {"status": "unhealthy", "message": f"Ошибка проверки здоровья: {str(e)}"}
