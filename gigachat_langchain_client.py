import logging
from typing import Optional
from gigachat import GigaChat

logger = logging.getLogger(__name__)

class GigaChatLangChainClient:
    def __init__(self, credentials: str):
        self.credentials = credentials
        self.client: Optional[GigaChat] = None
    
    def _get_client(self) -> GigaChat:
        if not self.client:
            logger.info("Creating new GigaChat LangChain client...")
            self.client = GigaChat(
                credentials=self.credentials,
                verify_ssl_certs=False
            )
        return self.client
    
    def generate(self, prompt: str) -> str:
        logger.info(f"Generating response with LangChain client for prompt: {prompt[:100]}...")
        try:
            with self._get_client() as giga:
                logger.info("Making request to GigaChat via LangChain...")
                response = giga.chat(prompt)
                result = response.choices[0].message.content
                logger.info("GigaChat LangChain response received successfully")
                return result
        except Exception as e:
            logger.error(f"Failed to generate response with LangChain client: {str(e)}")
            raise
    
    def extract_material_info(self, text: str) -> str:
        logger.info(f"Extracting material info with LangChain client from text: {text[:100]}...")
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
        
        try:
            with self._get_client() as giga:
                logger.info("Making extract request to GigaChat via LangChain...")
                response = giga.chat(base_prompt)
                result = response.choices[0].message.content
                logger.info("Material info extracted successfully with LangChain")
                return result
        except Exception as e:
            logger.error(f"Failed to extract material info with LangChain client: {str(e)}")
            raise
