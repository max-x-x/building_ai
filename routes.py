from fastapi import APIRouter, HTTPException
from gigachat_client import GigaChatClient
from building_api_client import BuildingAPIClient
from models import GenerateRequest, ExtractRequest, ObjectQuestionRequest

router = APIRouter()

gigachat_client = GigaChatClient()
building_client = BuildingAPIClient()

@router.get("/ping")
async def ping():
    return {"status": "ok", "message": "Server is running"}

@router.post("/generate")
async def generate_text(request: GenerateRequest):
    try:
        result = gigachat_client.generate(request.prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract")
async def extract_materials(request: ExtractRequest):
    try:
        result = gigachat_client.extract_material_info(request.text)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/object_question")
async def answer_object_question(request: ObjectQuestionRequest):
    try:
        if not building_client.token:
            login_result = building_client.login("admin@gmail.com", "111")
            if "error" in login_result:
                raise HTTPException(status_code=500, detail=f"Authentication error: {login_result['error']}")
        
        object_data = building_client.get_object_full(request.object_id)
        if "error" in object_data:
            raise HTTPException(status_code=500, detail=f"Object data error: {object_data['error']}")
        
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
        
        result = gigachat_client.generate(prompt)
        return {"result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
