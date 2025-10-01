from pydantic import BaseModel

class GenerateRequest(BaseModel):
    prompt: str

class ExtractRequest(BaseModel):
    text: str

class ObjectQuestionRequest(BaseModel):
    object_id: str
    question: str
