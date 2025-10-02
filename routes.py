import logging
from fastapi import APIRouter, HTTPException
from gigachat_client import GigaChatClient
from building_api_client import BuildingAPIClient
from models import GenerateRequest, ExtractRequest, ObjectQuestionRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

gigachat_client = GigaChatClient()
building_client = BuildingAPIClient()

@router.get("/ping")
async def ping():
    logger.info("Ping endpoint called")
    return {"status": "ok", "message": "Server is running"}

@router.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    try:
        gigachat_health = gigachat_client.health_check()
        return {
            "status": "ok",
            "services": {
                "gigachat": gigachat_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/generate")
async def generate_text(request: GenerateRequest):
    logger.info(f"Generate endpoint called with prompt: {request.prompt[:50]}...")
    try:
        logger.info("Calling GigaChat client...")
        result = gigachat_client.generate(request.prompt)
        logger.info("GigaChat response received successfully")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        fallback_response = f"Извините, сервис GigaChat временно недоступен. Ваш запрос: '{request.prompt}'"
        logger.warning("Returning fallback response due to GigaChat unavailability")
        return {"result": fallback_response}

@router.post("/extract")
async def extract_materials(request: ExtractRequest):
    logger.info(f"Extract endpoint called with text: {request.text[:50]}...")
    try:
        logger.info("Calling GigaChat extract_material_info...")
        result = gigachat_client.extract_material_info(request.text)
        logger.info("Extract response received successfully")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in extract endpoint: {str(e)}")
        fallback_response = '{"Наименование материала": "Неизвестно", "Количество материала": "Неизвестно", "Размер": "", "Объем": "", "Нетто": ""}'
        logger.warning("Returning fallback response due to GigaChat unavailability")
        return {"result": fallback_response}

@router.post("/object_question")
async def answer_object_question(request: ObjectQuestionRequest):
    logger.info(f"Object question endpoint called with object_id: {request.object_id}, question: {request.question[:50]}...")
    try:
        if not building_client.token:
            logger.info("No building client token, attempting login...")
            login_result = building_client.login("admin@gmail.com", "111")
            if "error" in login_result:
                logger.error(f"Building API login failed: {login_result['error']}")
                raise HTTPException(status_code=500, detail=f"Authentication error: {login_result['error']}")
            logger.info("Building API login successful")
        
        logger.info(f"Getting object data for ID: {request.object_id}")
        object_data = building_client.get_object_full(request.object_id)
        if "error" in object_data:
            logger.error(f"Failed to get object data: {object_data['error']}")
            raise HTTPException(status_code=500, detail=f"Object data error: {object_data['error']}")
        logger.info("Object data retrieved successfully")
        
        logger.info("Generating prompt for GigaChat...")
        prompt = f"""Ты - эксперт по строительным объектам. Ответь на вопрос пользователя на основе предоставленной информации об объекте.

Вопрос: {request.question}

Информация об объекте:
- Название: {object_data.get('name', 'Не указано')}
- Адрес: {object_data.get('address', 'Не указано')}
- Статус: {object_data.get('status', 'Не указано')}
- Прогресс работ: {object_data.get('work_progress', 0)}%
- Участники проекта:
  * ССК: {object_data.get('ssk', {}).get('full_name', 'Не назначен')}
  * Прораб: {object_data.get('foreman', {}).get('full_name', 'Не назначен')}
  * ИКО: {object_data.get('iko', {}).get('full_name', 'Не назначен')}

Планы работ:
{object_data.get('work_plans', [])}

Поставки:
{object_data.get('deliveries', [])}

Нарушения:
{object_data.get('prescriptions', [])}

Активации:
{object_data.get('activations', [])}

Дай подробный и полезный ответ на вопрос пользователя, используя информацию об объекте."""
        
        logger.info("Calling GigaChat for object question...")
        result = gigachat_client.generate(prompt)
        logger.info("Object question response received successfully")
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Error in object_question endpoint: {str(e)}")
        fallback_response = f"Извините, сервис GigaChat временно недоступен. Ваш запрос по объекту '{request.object_id}': '{request.question}'"
        logger.warning("Returning fallback response due to GigaChat unavailability")
        return {"result": fallback_response}
