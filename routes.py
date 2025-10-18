import logging
import requests
from fastapi import APIRouter, HTTPException
from gigachat_client import GigaChatClient
from models import GenerateRequest, ExtractRequest, ObjectQuestionRequest
from utils import extract_object_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

gigachat_client = GigaChatClient()

@router.get("/ping")
async def ping():
    logger.info("Ping endpoint called")
    return {"status": "ok", "message": "Server is running"}


@router.post("/generate")
async def generate_text(request: GenerateRequest):
    try:
        result = gigachat_client.generate(request.prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/extract")
async def extract_materials(request: ExtractRequest):
    try:
        result = gigachat_client.extract_material_info(request.text)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/object_question")
async def answer_object_question(request: ObjectQuestionRequest):
    try:
        result = gigachat_client.answer_object_question(request.object_id, request.token, request.question)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

